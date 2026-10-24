import os
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.api.deps import (
    get_db,
    get_current_user,
    require_viewer_or_higher,
    require_accountant_or_higher,
    require_finance_manager_or_higher,
)
from app.core.audit import record_audit_log
from app.models.user import User
from app.models.membership import BusinessMembership
from app.models.file import UploadedFile, FileStatus
from app.models.account import FinancialAccount
from app.models.import_job import (
    ImportJob, 
    ImportJobStatus, 
    ImportMapping, 
    ImportValidationResult
)
from app.models.transaction import ImportedRecord
from app.services.csv_parser import parse_csv_file
from app.services.excel_parser import parse_excel_file
from app.services.column_detector import detect_column_mappings
from app.services.validator import validate_all_rows
from app.services.extraction.pdf_extractor import PDFDocumentExtractor
from app.services.extraction.image_extractor import ImageDocumentExtractor
from app.schemas.import_job import (
    ColumnSuggestionOut,
    ImportMappingRequest,
    ImportValidationSummary,
    ValidationRowResult,
    ImportJobOut,
    ImportConfirmResponse,
    ImportedRecordOut,
)

router = APIRouter()

def parse_file_by_type(file_path: str, ext: str):
    ext = ext.lower()
    if ext == ".csv":
        return parse_csv_file(file_path)
    elif ext in (".xlsx", ".xls"):
        return parse_excel_file(file_path)
    elif ext == ".pdf":
        extractor = PDFDocumentExtractor()
        res = extractor.extract(file_path)
        return res.headers, res.structured_rows
    elif ext in (".png", ".jpg", ".jpeg"):
        extractor = ImageDocumentExtractor()
        res = extractor.extract(file_path)
        return res.headers, res.structured_rows
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format '{ext}'.")

@router.post("/{business_id}/imports/start", response_model=dict)
def start_import_job(
    business_id: str,
    upload_id: str,
    membership: BusinessMembership = Depends(require_accountant_or_higher),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Step 1 & 2: Inspects uploaded file, detects columns, suggests mappings.
    """
    uploaded_file = (
        db.query(UploadedFile)
        .filter(
            UploadedFile.id == upload_id,
            UploadedFile.business_id == business_id
        )
        .first()
    )
    if not uploaded_file:
        raise HTTPException(status_code=404, detail="Uploaded file record not found.")

    _, ext = os.path.splitext(uploaded_file.stored_filename)
    ext = ext.lower()

    file_type_map = {
        ".csv": "CSV",
        ".xlsx": "EXCEL",
        ".xls": "EXCEL",
        ".pdf": "PDF",
        ".png": "IMAGE",
        ".jpg": "IMAGE",
        ".jpeg": "IMAGE",
    }
    file_type = file_type_map.get(ext, "UNKNOWN")

    try:
        headers, rows = parse_file_by_type(uploaded_file.file_path, ext)
    except Exception as e:
        uploaded_file.status = FileStatus.FAILED
        uploaded_file.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=400, detail=f"Failed to inspect file: {str(e)}")

    sample_rows = rows[:5] if rows else []
    suggested_mappings, suggested_date_format = detect_column_mappings(headers, sample_rows)

    # Create new import job
    job = ImportJob(
        business_id=business_id,
        uploaded_file_id=uploaded_file.id,
        created_by_user_id=current_user.id,
        file_type=file_type,
        status=ImportJobStatus.PENDING_MAPPING,
        total_rows=len(rows),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    return {
        "job_id": job.id,
        "file_type": file_type,
        "headers": headers,
        "sample_rows": sample_rows,
        "suggested_mappings": suggested_mappings,
        "suggested_date_format": suggested_date_format,
        "total_rows_detected": len(rows),
    }

@router.post("/{business_id}/imports/{job_id}/mapping", response_model=ImportValidationSummary)
def apply_mapping_and_validate(
    business_id: str,
    job_id: str,
    req: ImportMappingRequest,
    membership: BusinessMembership = Depends(require_accountant_or_higher),
    db: Session = Depends(get_db)
):
    """
    Step 3, 4 & 5: Apply user-adjusted mappings and run validation on all rows.
    """
    job = (
        db.query(ImportJob)
        .filter(ImportJob.id == job_id, ImportJob.business_id == business_id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found.")

    uploaded_file = job.uploaded_file
    _, ext = os.path.splitext(uploaded_file.stored_filename)
    headers, rows = parse_file_by_type(uploaded_file.file_path, ext)

    # Save or update ImportMapping
    mapping = db.query(ImportMapping).filter(ImportMapping.import_job_id == job.id).first()
    if not mapping:
        mapping = ImportMapping(
            import_job_id=job.id,
            column_mappings=req.column_mappings,
            date_format=req.date_format,
            custom_rules=req.custom_rules,
        )
        db.add(mapping)
    else:
        mapping.column_mappings = req.column_mappings
        mapping.date_format = req.date_format
        mapping.custom_rules = req.custom_rules

    if req.account_id:
        # Validate account belongs to this business
        acc = (
            db.query(FinancialAccount)
            .filter(
                FinancialAccount.id == req.account_id,
                FinancialAccount.business_id == business_id
            )
            .first()
        )
        if not acc:
            raise HTTPException(status_code=400, detail="Specified account not found in this business.")
        job.account_id = req.account_id

    # Run validation
    business = job.business
    valid_count, invalid_count, validation_results = validate_all_rows(
        rows=rows,
        mappings=req.column_mappings,
        preferred_date_format=req.date_format,
        default_currency=business.currency
    )

    # Clear prior validation results if any
    db.query(ImportValidationResult).filter(ImportValidationResult.import_job_id == job.id).delete()

    for item in validation_results:
        vr = ImportValidationResult(
            import_job_id=job.id,
            row_index=item["row_index"],
            raw_data=item["raw_data"],
            parsed_data=item["parsed_data"],
            is_valid=item["is_valid"],
            validation_errors=item["errors"],
        )
        db.add(vr)

    job.status = ImportJobStatus.READY_FOR_PREVIEW
    job.total_rows = len(rows)
    job.valid_rows = valid_count
    job.invalid_rows = invalid_count
    db.commit()
    db.refresh(job)

    preview_items = [
        ValidationRowResult(
            row_index=item["row_index"],
            is_valid=item["is_valid"],
            errors=item["errors"],
            warnings=item["warnings"],
            parsed_data=item["parsed_data"],
            raw_data=item["raw_data"],
        )
        for item in validation_results[:100]  # preview first 100 rows
    ]

    return ImportValidationSummary(
        job_id=job.id,
        status=job.status,
        total_rows=job.total_rows,
        valid_rows=job.valid_rows,
        invalid_rows=job.invalid_rows,
        preview_rows=preview_items,
    )

@router.get("/{business_id}/imports/{job_id}/preview", response_model=ImportValidationSummary)
def get_import_preview(
    business_id: str,
    job_id: str,
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db)
):
    """
    Step 6: Show preview and row-level validation results.
    """
    job = (
        db.query(ImportJob)
        .filter(ImportJob.id == job_id, ImportJob.business_id == business_id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found.")

    results = (
        db.query(ImportValidationResult)
        .filter(ImportValidationResult.import_job_id == job.id)
        .order_by(ImportValidationResult.row_index.asc())
        .limit(200)
        .all()
    )

    preview_items = [
        ValidationRowResult(
            row_index=r.row_index,
            is_valid=r.is_valid,
            errors=r.validation_errors or [],
            warnings=[],
            parsed_data=r.parsed_data,
            raw_data=r.raw_data,
        )
        for r in results
    ]

    return ImportValidationSummary(
        job_id=job.id,
        status=job.status,
        total_rows=job.total_rows,
        valid_rows=job.valid_rows,
        invalid_rows=job.invalid_rows,
        preview_rows=preview_items,
    )

@router.post("/{business_id}/imports/{job_id}/confirm", response_model=ImportConfirmResponse)
def confirm_and_save_import(
    business_id: str,
    job_id: str,
    request: Request,
    membership: BusinessMembership = Depends(require_finance_manager_or_higher),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Step 7 & 8: Explicitly confirm import and store approved records with full provenance.
    Requires FINANCE_MANAGER or OWNER role.
    """
    job = (
        db.query(ImportJob)
        .filter(ImportJob.id == job_id, ImportJob.business_id == business_id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found.")

    if job.status == ImportJobStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This import job has already been approved and confirmed."
        )

    # Fetch all valid rows
    valid_results = (
        db.query(ImportValidationResult)
        .filter(
            ImportValidationResult.import_job_id == job.id,
            ImportValidationResult.is_valid == True
        )
        .all()
    )

    if not valid_results:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot confirm import: There are no valid records in this job."
        )

    saved_count = 0
    for vr in valid_results:
        p = vr.parsed_data
        if not p:
            continue
        rec = ImportedRecord(
            business_id=business_id,
            account_id=job.account_id,
            import_job_id=job.id,
            row_index=vr.row_index,
            transaction_date=datetime.fromisoformat(p["transaction_date"]).date(),
            description=p["description"],
            reference_number=p.get("reference_number"),
            debit=p.get("debit"),
            credit=p.get("credit"),
            amount=p["amount"],
            currency=p.get("currency", "INR"),
            raw_source_row=vr.raw_data,
        )
        db.add(rec)
        saved_count += 1

    job.status = ImportJobStatus.APPROVED
    job.completed_at = datetime.now(timezone.utc)
    
    # Mark uploaded file as processed
    if job.uploaded_file:
        job.uploaded_file.status = FileStatus.PROCESSED

    db.commit()

    record_audit_log(
        db=db,
        action="IMPORT_CONFIRMED",
        business_id=business_id,
        user_id=current_user.id,
        resource_type="ImportJob",
        resource_id=job.id,
        details={
            "imported_count": saved_count,
            "account_id": job.account_id,
            "filename": job.uploaded_file.original_filename if job.uploaded_file else None,
        },
        ip_address=request.client.host if request.client else None,
    )

    return ImportConfirmResponse(
        success=True,
        imported_count=saved_count,
        message=f"Successfully imported {saved_count} financial transactions."
    )

@router.get("/{business_id}/imports", response_model=List[ImportJobOut])
def list_import_jobs(
    business_id: str,
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db)
):
    jobs = (
        db.query(ImportJob)
        .filter(ImportJob.business_id == business_id)
        .order_by(ImportJob.created_at.desc())
        .all()
    )
    return jobs

@router.get("/{business_id}/records", response_model=List[ImportedRecordOut])
def list_imported_records(
    business_id: str,
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db)
):
    records = (
        db.query(ImportedRecord)
        .filter(ImportedRecord.business_id == business_id)
        .order_by(ImportedRecord.transaction_date.desc(), ImportedRecord.created_at.desc())
        .limit(200)
        .all()
    )
    return records

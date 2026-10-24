from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.orm import Session
from app.api.deps import (
    get_db,
    get_current_user,
    require_viewer_or_higher,
    require_accountant_or_higher,
)
from app.core.audit import record_audit_log
from app.core.storage import StorageManager
from app.models.user import User
from app.models.membership import BusinessMembership
from app.models.file import UploadedFile, FileStatus
from app.models.import_job import ImportJob, ImportJobStatus
from app.schemas.file import UploadedFileOut
from app.schemas.batch_upload import BatchUploadResponse, BatchFileResult

router = APIRouter()

@router.post("/{business_id}/uploads", response_model=UploadedFileOut, status_code=status.HTTP_201_CREATED)
async def upload_financial_file(
    business_id: str,
    request: Request,
    file: UploadFile = File(...),
    membership: BusinessMembership = Depends(require_accountant_or_higher),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Save and validate file safely
    stored_filename, file_path, file_size, mime_type, file_hash = await StorageManager.save_uploaded_file(file)

    # Check for duplicate file within this business
    existing_duplicate = (
        db.query(UploadedFile)
        .filter(
            UploadedFile.business_id == business_id,
            UploadedFile.file_hash == file_hash
        )
        .first()
    )
    if existing_duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Duplicate upload detected: An identical file ('{existing_duplicate.original_filename}') was previously uploaded on {existing_duplicate.created_at.strftime('%Y-%m-%d %H:%M:%S')}."
        )

    uploaded_record = UploadedFile(
        business_id=business_id,
        uploader_user_id=current_user.id,
        original_filename=file.filename or "uploaded_file",
        stored_filename=stored_filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=mime_type,
        file_hash=file_hash,
        status=FileStatus.UPLOADED,
    )
    db.add(uploaded_record)
    db.commit()
    db.refresh(uploaded_record)

    record_audit_log(
        db=db,
        action="FILE_UPLOADED",
        business_id=business_id,
        user_id=current_user.id,
        resource_type="UploadedFile",
        resource_id=uploaded_record.id,
        details={
            "filename": uploaded_record.original_filename,
            "size": uploaded_record.file_size,
            "mime_type": uploaded_record.mime_type
        },
        ip_address=request.client.host if request.client else None,
    )

    return uploaded_record


@router.post("/{business_id}/uploads/batch", response_model=BatchUploadResponse, status_code=status.HTTP_200_OK)
async def upload_multiple_financial_files(
    business_id: str,
    request: Request,
    files: List[UploadFile] = File(...),
    membership: BusinessMembership = Depends(require_accountant_or_higher),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Multi-file batch upload endpoint supporting concurrent statement/receipt uploads.
    Enforces per-file validation and safe isolation so that partial failures do not reject
    valid files in the same batch.
    """
    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 files can be uploaded simultaneously in a single batch."
        )

    results: List[BatchFileResult] = []
    successful_count = 0
    failed_count = 0

    for upload_file in files:
        filename = upload_file.filename or "uploaded_file"
        try:
            stored_filename, file_path, file_size, mime_type, file_hash = await StorageManager.save_uploaded_file(upload_file)

            # Check duplicate within this tenant
            existing = (
                db.query(UploadedFile)
                .filter(
                    UploadedFile.business_id == business_id,
                    UploadedFile.file_hash == file_hash
                )
                .first()
            )
            if existing:
                results.append(BatchFileResult(
                    filename=filename,
                    file_size=file_size,
                    status="FAILED",
                    mime_type=mime_type,
                    error_message=f"Duplicate file: Previously uploaded on {existing.created_at.strftime('%Y-%m-%d')}."
                ))
                failed_count += 1
                continue

            # Record uploaded file
            uploaded_record = UploadedFile(
                business_id=business_id,
                uploader_user_id=current_user.id,
                original_filename=filename,
                stored_filename=stored_filename,
                file_path=file_path,
                file_size=file_size,
                mime_type=mime_type,
                file_hash=file_hash,
                status=FileStatus.UPLOADED,
            )
            db.add(uploaded_record)
            db.flush()

            # Create independent import job for this file
            ext_type = "CSV" if "csv" in (mime_type or "") else ("EXCEL" if ("excel" in (mime_type or "") or "spreadsheet" in (mime_type or "")) else "PDF")
            import_job = ImportJob(
                business_id=business_id,
                uploaded_file_id=uploaded_record.id,
                created_by_user_id=current_user.id,
                file_type=ext_type,
                status=ImportJobStatus.PENDING_MAPPING
            )
            db.add(import_job)
            db.flush()

            record_audit_log(
                db=db,
                action="BATCH_FILE_UPLOADED",
                business_id=business_id,
                user_id=current_user.id,
                resource_type="UploadedFile",
                resource_id=uploaded_record.id,
                details={
                    "filename": filename,
                    "size": file_size,
                    "mime_type": mime_type,
                    "import_job_id": import_job.id
                },
                ip_address=request.client.host if request.client else None,
            )

            results.append(BatchFileResult(
                filename=filename,
                file_size=file_size,
                status="SUCCESS",
                mime_type=mime_type,
                upload_id=uploaded_record.id,
                import_job_id=import_job.id
            ))
            successful_count += 1

        except HTTPException as he:
            results.append(BatchFileResult(
                filename=filename,
                file_size=0,
                status="FAILED",
                error_message=he.detail
            ))
            failed_count += 1
        except Exception as e:
            results.append(BatchFileResult(
                filename=filename,
                file_size=0,
                status="FAILED",
                error_message=str(e)
            ))
            failed_count += 1

    db.commit()

    return BatchUploadResponse(
        total_files=len(files),
        successful_count=successful_count,
        failed_count=failed_count,
        results=results
    )


@router.get("/{business_id}/uploads", response_model=List[UploadedFileOut])
def list_uploads(
    business_id: str,
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db)
):
    records = (
        db.query(UploadedFile)
        .filter(UploadedFile.business_id == business_id)
        .order_by(UploadedFile.created_at.desc())
        .all()
    )
    return records

@router.get("/{business_id}/uploads/{upload_id}", response_model=UploadedFileOut)
def get_upload(
    business_id: str,
    upload_id: str,
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db)
):
    record = (
        db.query(UploadedFile)
        .filter(
            UploadedFile.id == upload_id,
            UploadedFile.business_id == business_id
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Uploaded file record not found.")
    return record

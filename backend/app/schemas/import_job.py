from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.models.import_job import ImportJobStatus

class ColumnSuggestionOut(BaseModel):
    headers: List[str]
    sample_rows: List[Dict[str, Any]]
    suggested_mappings: Dict[str, Optional[str]]  # e.g., {"date": "Trans Date", "description": "Narration", ...}
    suggested_date_format: Optional[str] = None
    file_type: str

class ImportMappingRequest(BaseModel):
    account_id: Optional[str] = None
    column_mappings: Dict[str, Optional[str]]  # Standard fields: date, description, amount, debit, credit, reference, currency
    date_format: Optional[str] = "%d/%m/%Y"
    custom_rules: Optional[Dict[str, Any]] = None

class ValidationRowResult(BaseModel):
    row_index: int
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    parsed_data: Optional[Dict[str, Any]] = None
    raw_data: Dict[str, Any]

class ImportValidationSummary(BaseModel):
    job_id: str
    status: ImportJobStatus
    total_rows: int
    valid_rows: int
    invalid_rows: int
    preview_rows: List[ValidationRowResult]

class ImportJobOut(BaseModel):
    id: str
    business_id: str
    account_id: Optional[str] = None
    uploaded_file_id: str
    file_type: str
    status: ImportJobStatus
    total_rows: int
    valid_rows: int
    invalid_rows: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ImportConfirmResponse(BaseModel):
    success: bool
    imported_count: int
    message: str

class ImportedRecordOut(BaseModel):
    id: str
    business_id: str
    account_id: Optional[str] = None
    import_job_id: str
    row_index: int
    transaction_date: date
    description: str
    reference_number: Optional[str] = None
    debit: Optional[float] = None
    credit: Optional[float] = None
    amount: float
    currency: str
    created_at: datetime

    class Config:
        from_attributes = True

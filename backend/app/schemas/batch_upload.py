from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class BatchFileResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    filename: str
    file_size: int
    status: str  # "SUCCESS" or "FAILED"
    mime_type: Optional[str] = None
    upload_id: Optional[str] = None
    import_job_id: Optional[str] = None
    error_message: Optional[str] = None

class BatchUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_files: int
    successful_count: int
    failed_count: int
    results: List[BatchFileResult]

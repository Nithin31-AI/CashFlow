from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.file import FileStatus

class UploadedFileOut(BaseModel):
    id: str
    business_id: str
    uploader_user_id: Optional[str] = None
    original_filename: str
    file_size: int
    mime_type: str
    file_hash: str
    status: FileStatus
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

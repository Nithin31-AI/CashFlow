import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db.session import Base

def generate_uuid() -> str:
    return uuid.uuid4().hex

class FileStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"

class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    uploader_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_hash = Column(String(64), index=True, nullable=False)  # SHA256
    status = Column(SQLEnum(FileStatus), default=FileStatus.UPLOADED, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    business = relationship("Business", back_populates="uploaded_files")
    uploader = relationship("User")
    import_jobs = relationship("ImportJob", back_populates="uploaded_file", cascade="all, delete-orphan")

import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base

def generate_uuid() -> str:
    return uuid.uuid4().hex

class ImportJobStatus(str, enum.Enum):
    PENDING_MAPPING = "PENDING_MAPPING"
    VALIDATING = "VALIDATING"
    READY_FOR_PREVIEW = "READY_FOR_PREVIEW"
    APPROVED = "APPROVED"
    FAILED = "FAILED"

class ImportJob(Base):
    __tablename__ = "import_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(String(36), ForeignKey("financial_accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    uploaded_file_id = Column(String(36), ForeignKey("uploaded_files.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    file_type = Column(String(50), nullable=False)  # CSV, EXCEL, PDF, IMAGE
    status = Column(SQLEnum(ImportJobStatus), default=ImportJobStatus.PENDING_MAPPING, nullable=False)
    total_rows = Column(Integer, default=0, nullable=False)
    valid_rows = Column(Integer, default=0, nullable=False)
    invalid_rows = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    business = relationship("Business", back_populates="import_jobs")
    account = relationship("FinancialAccount", back_populates="import_jobs")
    uploaded_file = relationship("UploadedFile", back_populates="import_jobs")
    created_by = relationship("User")
    mapping = relationship("ImportMapping", back_populates="import_job", uselist=False, cascade="all, delete-orphan")
    validation_results = relationship("ImportValidationResult", back_populates="import_job", cascade="all, delete-orphan")
    records = relationship("ImportedRecord", back_populates="import_job", cascade="all, delete-orphan")

class ImportMapping(Base):
    __tablename__ = "import_mappings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    import_job_id = Column(String(36), ForeignKey("import_jobs.id", ondelete="CASCADE"), unique=True, nullable=False)
    column_mappings = Column(JSON, nullable=False)  # e.g., {"date": "Transaction Date", "description": "Particulars", "amount": "Amount", "debit": "Withdrawal", "credit": "Deposit", "reference": "Ref No"}
    date_format = Column(String(50), nullable=True)  # e.g., '%d/%m/%Y'
    custom_rules = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    import_job = relationship("ImportJob", back_populates="mapping")

class ImportValidationResult(Base):
    __tablename__ = "import_validation_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    import_job_id = Column(String(36), ForeignKey("import_jobs.id", ondelete="CASCADE"), index=True, nullable=False)
    row_index = Column(Integer, nullable=False)
    raw_data = Column(JSON, nullable=False)
    parsed_data = Column(JSON, nullable=True)
    is_valid = Column(Boolean, nullable=False)
    validation_errors = Column(JSON, nullable=True)  # List of error message strings
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    import_job = relationship("ImportJob", back_populates="validation_results")

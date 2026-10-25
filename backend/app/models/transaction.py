import uuid
import enum
from datetime import datetime, timezone, date
from sqlalchemy import Column, String, Integer, Date, Text, Numeric, DateTime, ForeignKey, JSON, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db.session import Base

def generate_uuid() -> str:
    return uuid.uuid4().hex

class TransactionType(str, enum.Enum):
    INFLOW = "INFLOW"
    OUTFLOW = "OUTFLOW"
    INTERNAL_TRANSFER = "INTERNAL_TRANSFER"
    ADJUSTMENT = "ADJUSTMENT"

class TransactionCategory(str, enum.Enum):
    REVENUE = "REVENUE"
    PAYROLL = "PAYROLL"
    RENT = "RENT"
    SOFTWARE = "SOFTWARE"
    CONSULTING = "CONSULTING"
    UTILITIES = "UTILITIES"
    MARKETING = "MARKETING"
    TAX = "TAX"
    OFFICE_SUPPLIES = "OFFICE_SUPPLIES"
    TRAVEL = "TRAVEL"
    INTERNAL_TRANSFER = "INTERNAL_TRANSFER"
    OTHER = "OTHER"

class TransactionStatus(str, enum.Enum):
    POSTED = "POSTED"
    PENDING = "PENDING"
    RECONCILED = "RECONCILED"


class ImportedRecord(Base):
    """
    Financial records confirmed and approved from an import job.
    Includes full provenance back to source import job and original row.
    """
    __tablename__ = "imported_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(String(36), ForeignKey("financial_accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    import_job_id = Column(String(36), ForeignKey("import_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    row_index = Column(Integer, nullable=False)
    
    transaction_date = Column(Date, nullable=False, index=True)
    description = Column(Text, nullable=False)
    reference_number = Column(String(100), nullable=True)
    debit = Column(Numeric(15, 2), nullable=True)
    credit = Column(Numeric(15, 2), nullable=True)
    amount = Column(Numeric(15, 2), nullable=False)  # Net amount (positive = inflow, negative = outflow)
    currency = Column(String(10), default="INR", nullable=False)
    
    raw_source_row = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    business = relationship("Business", back_populates="records")
    account = relationship("FinancialAccount", back_populates="records")
    import_job = relationship("ImportJob", back_populates="records")
    transaction = relationship("Transaction", back_populates="imported_record", uselist=False)


class Transaction(Base):
    """
    Comprehensive financial ledger transactions.
    Supports internal transfers, category classifications, and reconciliation status.
    """
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(String(36), ForeignKey("financial_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    imported_record_id = Column(String(36), ForeignKey("imported_records.id", ondelete="SET NULL"), nullable=True, index=True)
    payment_id = Column(String(36), ForeignKey("payments.id", ondelete="SET NULL"), nullable=True, unique=True, index=True)
    
    transaction_date = Column(Date, nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)  # Positive for inflow, Negative for outflow
    currency = Column(String(10), default="INR", nullable=False)
    description = Column(Text, nullable=False)
    
    category = Column(SQLEnum(TransactionCategory), default=TransactionCategory.OTHER, nullable=False, index=True)
    transaction_type = Column(SQLEnum(TransactionType), default=TransactionType.OUTFLOW, nullable=False, index=True)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.POSTED, nullable=False, index=True)
    
    is_internal_transfer = Column(Boolean, default=False, nullable=False, index=True)
    transfer_counterpart_id = Column(String(36), ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True)
    reference_number = Column(String(100), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    business = relationship("Business", back_populates="transactions")
    account = relationship("FinancialAccount", back_populates="transactions")
    imported_record = relationship("ImportedRecord", back_populates="transaction")
    payment = relationship("Payment", back_populates="transaction", uselist=False)
    reconciliation = relationship("ReconciliationRecord", back_populates="transaction", uselist=False)

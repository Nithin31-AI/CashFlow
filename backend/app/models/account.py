import uuid
import enum
from datetime import datetime, timezone, date
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Date, Numeric, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db.session import Base

def generate_uuid() -> str:
    return uuid.uuid4().hex

class AccountType(str, enum.Enum):
    BANK = "BANK"
    CREDIT_CARD = "CREDIT_CARD"
    WALLET = "WALLET"
    OTHER = "OTHER"

class FinancialAccount(Base):
    __tablename__ = "financial_accounts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    account_type = Column(SQLEnum(AccountType), default=AccountType.BANK, nullable=False)
    account_number_mask = Column(String(50), nullable=True)  # e.g., '•••• 8821'
    currency = Column(String(10), default="INR", nullable=False)
    institution_name = Column(String(255), nullable=True)
    
    opening_balance = Column(Numeric(15, 2), default=0.00, nullable=False)
    opening_balance_date = Column(Date, default=lambda: datetime.now(timezone.utc).date(), nullable=False)
    
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    business = relationship("Business", back_populates="accounts")
    import_jobs = relationship("ImportJob", back_populates="account")
    records = relationship("ImportedRecord", back_populates="account")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="account")

import uuid
import enum
from datetime import datetime, timezone, date
from sqlalchemy import Column, String, Integer, Date, Text, Numeric, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base

def generate_uuid() -> str:
    return uuid.uuid4().hex

class InvoiceStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"

class PaymentMethod(str, enum.Enum):
    BANK_TRANSFER = "BANK_TRANSFER"
    UPI = "UPI"
    CREDIT_CARD = "CREDIT_CARD"
    CASH = "CASH"
    CHEQUE = "CHEQUE"
    OTHER = "OTHER"

class Invoice(Base):
    """
    Customer invoices tracking receivables.
    Unpaid invoices are strictly kept separate from available cash.
    """
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("business_id", "invoice_number", name="uq_business_invoice_number"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_number = Column(String(100), nullable=False)
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=True)
    issue_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=False, index=True)
    currency = Column(String(10), default="INR", nullable=False)
    
    subtotal = Column(Numeric(15, 2), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=0.00, nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)
    amount_paid = Column(Numeric(15, 2), default=0.00, nullable=False)
    
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.DRAFT, nullable=False, index=True)
    expected_payment_date = Column(Date, nullable=True)
    predicted_delay_days = Column(Integer, default=0, nullable=False)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    business = relationship("Business", back_populates="invoices")
    allocations = relationship("InvoicePaymentAllocation", back_populates="invoice", cascade="all, delete-orphan")

    @property
    def paid_amount(self):
        return self.amount_paid


class Payment(Base):
    """
    Authoritative cash inflow payments received into accounts.
    """
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(String(36), ForeignKey("financial_accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    
    payment_date = Column(Date, nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    payment_method = Column(SQLEnum(PaymentMethod), default=PaymentMethod.BANK_TRANSFER, nullable=False)
    reference_number = Column(String(100), nullable=True, index=True)
    payer_name = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    
    unallocated_amount = Column(Numeric(15, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    business = relationship("Business", back_populates="payments")
    account = relationship("FinancialAccount", back_populates="payments")
    allocations = relationship("InvoicePaymentAllocation", back_populates="payment", cascade="all, delete-orphan")


class InvoicePaymentAllocation(Base):
    """
    Prevents double allocation of payments to invoices with unique constraints.
    """
    __tablename__ = "invoice_payment_allocations"
    __table_args__ = (
        UniqueConstraint("invoice_id", "payment_id", name="uq_invoice_payment_allocation"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    business_id = Column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id = Column(String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    payment_id = Column(String(36), ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, index=True)
    allocated_amount = Column(Numeric(15, 2), nullable=False)
    allocated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    business = relationship("Business")
    invoice = relationship("Invoice", back_populates="allocations")
    payment = relationship("Payment", back_populates="allocations")

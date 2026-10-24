from decimal import Decimal
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.invoice import InvoiceStatus, PaymentMethod

class InvoiceCreate(BaseModel):
    invoice_number: str
    customer_name: str
    customer_email: Optional[str] = None
    issue_date: date
    due_date: date
    currency: str = "INR"
    subtotal: Decimal
    tax_amount: Decimal = Decimal("0.00")
    total_amount: Decimal
    notes: Optional[str] = None

class AllocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    payment_id: str
    allocated_amount: Decimal
    allocated_at: datetime

class InvoiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    business_id: str
    invoice_number: str
    customer_name: str
    customer_email: Optional[str] = None
    issue_date: date
    due_date: date
    currency: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    status: str
    expected_payment_date: Optional[date] = None
    predicted_delay_days: int
    notes: Optional[str] = None
    created_at: datetime
    allocations: List[AllocationOut] = []

class PaymentCreate(BaseModel):
    account_id: Optional[str] = None
    invoice_id: Optional[str] = None  # Direct allocation if provided
    payment_date: date
    amount: Decimal
    currency: str = "INR"
    payment_method: PaymentMethod = PaymentMethod.BANK_TRANSFER
    reference_number: Optional[str] = None
    payer_name: Optional[str] = None
    notes: Optional[str] = None

class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    business_id: str
    account_id: Optional[str] = None
    payment_date: date
    amount: Decimal
    currency: str
    payment_method: str
    reference_number: Optional[str] = None
    payer_name: Optional[str] = None
    unallocated_amount: Decimal
    notes: Optional[str] = None
    created_at: datetime

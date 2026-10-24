from decimal import Decimal
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.transaction import TransactionCategory, TransactionType, TransactionStatus

class TransactionCreate(BaseModel):
    account_id: str
    transaction_date: date
    amount: Decimal
    currency: str = "INR"
    description: str
    category: TransactionCategory = TransactionCategory.OTHER
    transaction_type: TransactionType = TransactionType.OUTFLOW
    is_internal_transfer: bool = False
    transfer_counterpart_account_id: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None

class TransactionCategoryUpdate(BaseModel):
    category: TransactionCategory
    notes: Optional[str] = None

class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    business_id: str
    account_id: str
    transaction_date: date
    amount: Decimal
    currency: str
    description: str
    category: str
    transaction_type: str
    status: str
    is_internal_transfer: bool
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

from decimal import Decimal
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ReconciliationCandidateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reconciliation_id: str
    transaction_id: str
    transaction_date: date
    transaction_amount: Decimal
    transaction_description: str
    invoice_id: str
    invoice_number: str
    customer_name: str
    invoice_total: Decimal
    unpaid_amount: Decimal
    matched_amount: Decimal
    confidence_score: Decimal
    match_type: str
    status: str
    explanation: str

class ManualReconciliationCreate(BaseModel):
    transaction_id: str
    invoice_id: str
    amount: Decimal
    notes: Optional[str] = None

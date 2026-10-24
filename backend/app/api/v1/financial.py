from decimal import Decimal
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import (
    get_db,
    get_current_user,
    require_viewer_or_higher,
    require_finance_manager_or_higher
)
from app.models.user import User
from app.models.membership import BusinessMembership
from app.models.business import Business
from app.services.financial_service import FinancialService

router = APIRouter()

class ReserveUpdate(BaseModel):
    minimum_cash_reserve: Decimal

@router.get("/{business_id}/financial/overview")
def get_financial_overview(
    business_id: str,
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns consolidated verified financial position for the business workspace:
    - Actual liquid cash balance (separated from projections)
    - Minimum reserve and headroom
    - Outstanding and overdue receivables (unpaid invoices)
    - Revenue, expenses, net income (with internal transfers cleanly eliminated)
    - Breakdown per account
    """
    try:
        return FinancialService.get_business_financial_position(db, business_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{business_id}/financial/accounts/{account_id}/balance")
def get_account_balance(
    business_id: str,
    account_id: str,
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns authoritative decimal calculation:
    Ending balance = Opening Balance + Actual Inflows - Actual Outflows + Approved Adjustments.
    """
    try:
        return FinancialService.calculate_account_balance(db, account_id, business_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.patch("/{business_id}/financial/settings/reserve")
def update_minimum_reserve(
    business_id: str,
    payload: ReserveUpdate,
    membership: BusinessMembership = Depends(require_finance_manager_or_higher),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found.")

    business.minimum_cash_reserve = payload.minimum_cash_reserve
    db.commit()
    return {
        "status": "UPDATED",
        "minimum_cash_reserve": float(business.minimum_cash_reserve)
    }

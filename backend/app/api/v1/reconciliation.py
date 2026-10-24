from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_db,
    get_current_user,
    require_viewer_or_higher,
    require_finance_manager_or_higher,
)
from app.models.user import User
from app.models.membership import BusinessMembership
from app.services.reconciliation_service import ReconciliationService

router = APIRouter()

@router.get("/{business_id}/reconciliations/candidates")
def get_reconciliation_candidates(
    business_id: str,
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Scans unreconciled transactions and unpaid invoices to discover candidate matches
    with explainable confidence scoring.
    """
    return ReconciliationService.find_candidate_matches(db, business_id)


@router.post("/{business_id}/reconciliations/{reconciliation_id}/approve")
def approve_reconciliation_match(
    business_id: str,
    reconciliation_id: str,
    membership: BusinessMembership = Depends(require_finance_manager_or_higher),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Human review approval gate. Applies allocated payment, updates invoice status,
    and sets transaction to RECONCILED.
    """
    try:
        return ReconciliationService.approve_reconciliation(
            db=db,
            reconciliation_id=reconciliation_id,
            business_id=business_id,
            user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{business_id}/reconciliations/{reconciliation_id}/reject")
def reject_reconciliation_match(
    business_id: str,
    reconciliation_id: str,
    membership: BusinessMembership = Depends(require_finance_manager_or_higher),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    try:
        return ReconciliationService.reject_reconciliation(
            db=db,
            reconciliation_id=reconciliation_id,
            business_id=business_id,
            user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

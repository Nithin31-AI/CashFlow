from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.api.deps import (
    get_db,
    get_current_user,
    require_viewer_or_higher,
    require_finance_manager_or_higher,
)
from app.core.audit import record_audit_log
from app.models.user import User
from app.models.membership import BusinessMembership
from app.models.account import FinancialAccount
from app.schemas.account import (
    AccountCreate,
    AccountUpdate,
    AccountOut,
)

router = APIRouter()

@router.get("/{business_id}/accounts", response_model=List[AccountOut])
def list_accounts(
    business_id: str,
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db)
):
    accounts = (
        db.query(FinancialAccount)
        .filter(FinancialAccount.business_id == business_id)
        .order_by(FinancialAccount.created_at.asc())
        .all()
    )
    return accounts

@router.post("/{business_id}/accounts", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
def create_account(
    business_id: str,
    req: AccountCreate,
    request: Request,
    membership: BusinessMembership = Depends(require_finance_manager_or_higher),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    acc = FinancialAccount(
        business_id=business_id,
        name=req.name,
        account_type=req.account_type,
        account_number_mask=req.account_number_mask,
        currency=req.currency.upper(),
        institution_name=req.institution_name,
        is_active=True,
    )
    db.add(acc)
    db.commit()
    db.refresh(acc)

    record_audit_log(
        db=db,
        action="ACCOUNT_CREATED",
        business_id=business_id,
        user_id=current_user.id,
        resource_type="FinancialAccount",
        resource_id=acc.id,
        details={"name": acc.name, "type": acc.account_type.value},
        ip_address=request.client.host if request.client else None,
    )

    return acc

@router.patch("/{business_id}/accounts/{account_id}", response_model=AccountOut)
def update_account(
    business_id: str,
    account_id: str,
    req: AccountUpdate,
    request: Request,
    membership: BusinessMembership = Depends(require_finance_manager_or_higher),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    acc = (
        db.query(FinancialAccount)
        .filter(
            FinancialAccount.id == account_id,
            FinancialAccount.business_id == business_id
        )
        .first()
    )
    if not acc:
        raise HTTPException(status_code=404, detail="Financial account not found.")

    if req.name is not None:
        acc.name = req.name
    if req.account_type is not None:
        acc.account_type = req.account_type
    if req.account_number_mask is not None:
        acc.account_number_mask = req.account_number_mask
    if req.currency is not None:
        acc.currency = req.currency.upper()
    if req.institution_name is not None:
        acc.institution_name = req.institution_name
    if req.is_active is not None:
        acc.is_active = req.is_active

    db.commit()
    db.refresh(acc)

    record_audit_log(
        db=db,
        action="ACCOUNT_UPDATED",
        business_id=business_id,
        user_id=current_user.id,
        resource_type="FinancialAccount",
        resource_id=acc.id,
        details={"name": acc.name},
        ip_address=request.client.host if request.client else None,
    )

    return acc

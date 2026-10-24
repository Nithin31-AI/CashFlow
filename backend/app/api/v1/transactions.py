from decimal import Decimal
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from app.api.deps import (
    get_db,
    get_current_user,
    require_viewer_or_higher,
    require_accountant_or_higher,
)
from app.models.user import User
from app.models.membership import BusinessMembership
from app.models.transaction import Transaction, TransactionType, TransactionCategory, TransactionStatus
from app.models.account import FinancialAccount
from app.schemas.transaction import TransactionCreate, TransactionOut, TransactionCategoryUpdate

router = APIRouter()

@router.get("/{business_id}/transactions", response_model=List[TransactionOut])
def list_transactions(
    business_id: str,
    account_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    is_internal_transfer: Optional[bool] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db)
):
    query = db.query(Transaction).filter(Transaction.business_id == business_id)

    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    if category:
        query = query.filter(Transaction.category == category)
    if status:
        query = query.filter(Transaction.status == status)
    if is_internal_transfer is not None:
        query = query.filter(Transaction.is_internal_transfer == is_internal_transfer)
    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Transaction.description.ilike(search_filter),
                Transaction.reference_number.ilike(search_filter)
            )
        )

    records = query.order_by(desc(Transaction.transaction_date), desc(Transaction.created_at)).offset(offset).limit(limit).all()
    return records


@router.post("/{business_id}/transactions", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(
    business_id: str,
    payload: TransactionCreate,
    membership: BusinessMembership = Depends(require_accountant_or_higher),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify primary account
    account = db.query(FinancialAccount).filter(
        FinancialAccount.id == payload.account_id,
        FinancialAccount.business_id == business_id
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Primary financial account not found.")

    # Handle internal transfer between two accounts
    if payload.is_internal_transfer and payload.transfer_counterpart_account_id:
        dest_account = db.query(FinancialAccount).filter(
            FinancialAccount.id == payload.transfer_counterpart_account_id,
            FinancialAccount.business_id == business_id
        ).first()
        if not dest_account:
            raise HTTPException(status_code=404, detail="Destination counterpart account not found.")
        if dest_account.id == account.id:
            raise HTTPException(status_code=400, detail="Cannot perform internal transfer to the same account.")

        # Outflow from source account
        transfer_out = Transaction(
            business_id=business_id,
            account_id=account.id,
            transaction_date=payload.transaction_date,
            amount=-abs(payload.amount),
            currency=payload.currency,
            description=f"Transfer to {dest_account.name}: {payload.description}",
            category=TransactionCategory.INTERNAL_TRANSFER,
            transaction_type=TransactionType.INTERNAL_TRANSFER,
            status=TransactionStatus.POSTED,
            is_internal_transfer=True,
            reference_number=payload.reference_number,
            notes=payload.notes
        )
        db.add(transfer_out)
        db.flush()

        # Inflow to destination account
        transfer_in = Transaction(
            business_id=business_id,
            account_id=dest_account.id,
            transaction_date=payload.transaction_date,
            amount=abs(payload.amount),
            currency=payload.currency,
            description=f"Transfer from {account.name}: {payload.description}",
            category=TransactionCategory.INTERNAL_TRANSFER,
            transaction_type=TransactionType.INTERNAL_TRANSFER,
            status=TransactionStatus.POSTED,
            is_internal_transfer=True,
            transfer_counterpart_id=transfer_out.id,
            reference_number=payload.reference_number,
            notes=payload.notes
        )
        db.add(transfer_in)
        db.flush()

        transfer_out.transfer_counterpart_id = transfer_in.id
        db.commit()
        db.refresh(transfer_out)
        return transfer_out

    # Standard transaction
    tx = Transaction(
        business_id=business_id,
        account_id=account.id,
        transaction_date=payload.transaction_date,
        amount=payload.amount,
        currency=payload.currency,
        description=payload.description,
        category=payload.category,
        transaction_type=payload.transaction_type,
        status=TransactionStatus.POSTED,
        is_internal_transfer=payload.is_internal_transfer,
        reference_number=payload.reference_number,
        notes=payload.notes
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


@router.patch("/{business_id}/transactions/{transaction_id}/classification", response_model=TransactionOut)
def update_transaction_classification(
    business_id: str,
    transaction_id: str,
    payload: TransactionCategoryUpdate,
    membership: BusinessMembership = Depends(require_accountant_or_higher),
    db: Session = Depends(get_db)
):
    tx = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.business_id == business_id
    ).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found.")

    tx.category = payload.category
    if payload.notes:
        tx.notes = payload.notes
    db.commit()
    db.refresh(tx)
    return tx


@router.get("/{business_id}/transactions/meta/categories")
def get_transaction_categories(
    business_id: str,
    membership: BusinessMembership = Depends(require_viewer_or_higher)
):
    return [c.value for c in TransactionCategory]

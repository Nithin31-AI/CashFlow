from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api.deps import (
    get_db,
    get_current_user,
    require_viewer_or_higher,
    require_accountant_or_higher,
)
from app.models.user import User
from app.models.membership import BusinessMembership
from app.models.invoice import Invoice, InvoiceStatus, Payment, PaymentMethod, InvoicePaymentAllocation
from app.models.account import FinancialAccount, AccountType
from app.models.transaction import Transaction, TransactionType, TransactionCategory, TransactionStatus
from app.schemas.invoice import InvoiceCreate, InvoiceOut, PaymentCreate, PaymentOut, InvoiceStatusUpdate
from app.services.risk_service import RiskService
from app.services.financial_service import FinancialService

router = APIRouter()

@router.get("/{business_id}/invoices", response_model=List[InvoiceOut])
def list_invoices(
    business_id: str,
    status: Optional[str] = Query(None),
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db)
):
    query = db.query(Invoice).filter(Invoice.business_id == business_id)
    if status:
        query = query.filter(Invoice.status == status)
    
    invoices = query.order_by(desc(Invoice.due_date)).all()
    # Compute payment delay estimates
    RiskService.predict_invoice_payment_delays(db, business_id)
    return invoices


@router.post("/{business_id}/invoices", response_model=InvoiceOut, status_code=status.HTTP_201_CREATED)
def create_invoice(
    business_id: str,
    payload: InvoiceCreate,
    membership: BusinessMembership = Depends(require_accountant_or_higher),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check duplicate invoice number
    existing = db.query(Invoice).filter(
        Invoice.business_id == business_id,
        Invoice.invoice_number == payload.invoice_number
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invoice number '{payload.invoice_number}' already exists in this workspace."
        )

    invoice = Invoice(
        business_id=business_id,
        invoice_number=payload.invoice_number,
        customer_name=payload.customer_name,
        customer_email=payload.customer_email,
        issue_date=payload.issue_date,
        due_date=payload.due_date,
        currency=payload.currency,
        subtotal=payload.subtotal,
        tax_amount=payload.tax_amount,
        total_amount=payload.total_amount,
        amount_paid=Decimal("0.00"),
        status=InvoiceStatus.SENT,
        notes=payload.notes
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@router.get("/{business_id}/invoices/{invoice_id}", response_model=InvoiceOut)
def get_invoice_details(
    business_id: str,
    invoice_id: str,
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db)
):
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.business_id == business_id
    ).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    return invoice


@router.get("/{business_id}/payments", response_model=List[PaymentOut])
def list_payments(
    business_id: str,
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db)
):
    return db.query(Payment).filter(Payment.business_id == business_id).order_by(desc(Payment.payment_date)).all()


@router.post("/{business_id}/payments", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def record_payment(
    business_id: str,
    payload: PaymentCreate,
    membership: BusinessMembership = Depends(require_accountant_or_higher),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if payload.amount <= Decimal("0.00"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount must be greater than zero."
        )

    # 1. Resolve deposit account
    account = None
    if payload.account_id:
        account = db.query(FinancialAccount).filter(
            FinancialAccount.id == payload.account_id,
            FinancialAccount.business_id == business_id
        ).first()
        if not account:
            raise HTTPException(status_code=400, detail="Specified deposit account not found in this business.")
    else:
        # Default to business's primary active bank account
        account = db.query(FinancialAccount).filter(
            FinancialAccount.business_id == business_id,
            FinancialAccount.is_active == True,
            FinancialAccount.account_type == AccountType.BANK
        ).first()
        if not account:
            account = db.query(FinancialAccount).filter(
                FinancialAccount.business_id == business_id,
                FinancialAccount.is_active == True
            ).first()
        if account:
            payload.account_id = account.id

    # 2. Idempotency Check: prevent duplicate payment recording
    if payload.reference_number:
        duplicate_payment = db.query(Payment).filter(
            Payment.business_id == business_id,
            Payment.reference_number == payload.reference_number,
            Payment.amount == payload.amount
        ).first()
        if duplicate_payment:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Duplicate payment detected: A payment with reference '{payload.reference_number}' for amount {payload.amount} was already recorded."
            )

    allocated = Decimal("0.00")
    invoice = None

    if payload.invoice_id:
        invoice = db.query(Invoice).filter(
            Invoice.id == payload.invoice_id,
            Invoice.business_id == business_id
        ).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Specified invoice to allocate was not found.")

        if invoice.status == InvoiceStatus.PAID:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invoice '{invoice.invoice_number}' is already fully settled and marked PAID."
            )

        unpaid = Decimal(str(invoice.total_amount)) - Decimal(str(invoice.amount_paid or "0.00"))
        if unpaid <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invoice '{invoice.invoice_number}' has zero outstanding balance."
            )

        if payload.amount > unpaid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment amount ({payload.amount}) exceeds remaining balance of {unpaid} on invoice '{invoice.invoice_number}'."
            )

        allocated = min(payload.amount, unpaid)

    # 3. Create authoritative Payment record
    payment = Payment(
        business_id=business_id,
        account_id=payload.account_id,
        payment_date=payload.payment_date,
        amount=payload.amount,
        currency=payload.currency,
        payment_method=payload.payment_method,
        reference_number=payload.reference_number,
        payer_name=payload.payer_name or (invoice.customer_name if invoice else None),
        unallocated_amount=payload.amount - allocated,
        notes=payload.notes
    )
    db.add(payment)
    db.flush()

    # 4. Update Invoice status and allocation
    if invoice and allocated > 0:
        invoice.amount_paid = Decimal(str(invoice.amount_paid or "0.00")) + allocated
        if invoice.amount_paid >= invoice.total_amount:
            invoice.status = InvoiceStatus.PAID
        else:
            invoice.status = InvoiceStatus.PARTIALLY_PAID

        allocation = InvoicePaymentAllocation(
            business_id=business_id,
            invoice_id=invoice.id,
            payment_id=payment.id,
            allocated_amount=allocated
        )
        db.add(allocation)

    # 5. Create or associate exactly one corresponding financial ledger Transaction
    # Check if a matching unreconciled bank transaction already exists (avoid duplicate cash inflow)
    existing_tx = None
    if payload.reference_number and account:
        existing_tx = db.query(Transaction).filter(
            Transaction.business_id == business_id,
            Transaction.account_id == account.id,
            Transaction.reference_number == payload.reference_number,
            Transaction.amount == payload.amount,
            Transaction.payment_id.is_(None)
        ).first()

    if existing_tx:
        # Link existing transaction to this payment
        existing_tx.payment_id = payment.id
        existing_tx.category = TransactionCategory.REVENUE
        existing_tx.status = TransactionStatus.RECONCILED
    else:
        # Create authoritative new Transaction
        desc = f"Customer payment from {payment.payer_name or 'Customer'}" + (f" for invoice {invoice.invoice_number}" if invoice else "")
        tx = Transaction(
            business_id=business_id,
            account_id=account.id if account else None,
            payment_id=payment.id,
            transaction_date=payload.payment_date,
            amount=payload.amount,  # Positive cash inflow
            currency=payload.currency,
            description=desc,
            category=TransactionCategory.REVENUE,
            transaction_type=TransactionType.INFLOW,
            status=TransactionStatus.POSTED,
            reference_number=payload.reference_number,
            notes=payload.notes,
        )
        db.add(tx)
        db.flush()

    # 6. Recalculate and update account balance
    if account:
        acc_bal = FinancialService.calculate_account_balance(db, account.id, business_id)
        account.current_balance = acc_bal["current_balance"]

    db.commit()
    db.refresh(payment)
    return payment

@router.patch("/{business_id}/invoices/{invoice_id}/status", response_model=InvoiceOut)
def update_invoice_status(
    business_id: str,
    invoice_id: str,
    payload: InvoiceStatusUpdate,
    membership: BusinessMembership = Depends(require_accountant_or_higher),
    db: Session = Depends(get_db)
):
    """
    Enforces that changing an invoice to SENT does not create cash,
    and changing to PAID requires an actual recorded payment rather than arbitrary status mutation.
    """
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.business_id == business_id
    ).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found.")

    target = payload.status.upper().strip()
    if target == "PAID":
        unpaid = Decimal(str(invoice.total_amount)) - Decimal(str(invoice.amount_paid or "0.00"))
        if unpaid > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot mark invoice '{invoice.invoice_number}' as PAID directly. Outstanding balance is {invoice.currency} {unpaid}. An invoice changing to PAID represents actual settlement and requires recording a payment."
            )
        invoice.status = InvoiceStatus.PAID
    elif target in ["DRAFT", "SENT", "CANCELLED"]:
        invoice.status = InvoiceStatus[target]
    else:
        raise HTTPException(status_code=400, detail=f"Invalid invoice status '{new_status}'.")

    db.commit()
    db.refresh(invoice)
    return invoice


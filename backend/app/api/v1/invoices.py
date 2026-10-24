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
from app.models.account import FinancialAccount
from app.schemas.invoice import InvoiceCreate, InvoiceOut, PaymentCreate, PaymentOut
from app.services.risk_service import RiskService

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
    allocated = Decimal("0.00")
    invoice = None

    if payload.invoice_id:
        invoice = db.query(Invoice).filter(
            Invoice.id == payload.invoice_id,
            Invoice.business_id == business_id
        ).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Specified invoice to allocate was not found.")

        unpaid = Decimal(str(invoice.total_amount)) - Decimal(str(invoice.amount_paid or "0.00"))
        allocated = min(payload.amount, unpaid)

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

    db.commit()
    db.refresh(payment)
    return payment

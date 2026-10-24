from decimal import Decimal
from datetime import date
import uuid
import pytest
from app.models.business import Business
from app.models.account import FinancialAccount, AccountType
from app.models.transaction import Transaction, TransactionType, TransactionCategory, TransactionStatus
from app.models.invoice import Invoice, InvoiceStatus, Payment, InvoicePaymentAllocation
from app.models.reconciliation import ReconciliationRecord, ReconciliationStatus, MatchType
from app.services.reconciliation_service import ReconciliationService

def test_reconciliation_candidate_matching_and_approval(db_session, test_user):
    biz = Business(name="ReconTech", slug=f"retech-{uuid.uuid4().hex[:6]}", currency="INR")
    db_session.add(biz)
    db_session.flush()

    acc = FinancialAccount(business_id=biz.id, name="Current", account_type=AccountType.BANK)
    db_session.add(acc)
    db_session.flush()

    # Invoice for ACME Corp of 45000.00
    inv = Invoice(
        business_id=biz.id,
        invoice_number="INV-450",
        customer_name="ACME Corp",
        issue_date=date(2026, 1, 10),
        due_date=date(2026, 1, 25),
        subtotal=Decimal("45000.00"),
        total_amount=Decimal("45000.00"),
        amount_paid=Decimal("0.00"),
        status=InvoiceStatus.SENT
    )
    # Transaction received with exact amount and "ACME Corp INV-450" description
    tx = Transaction(
        business_id=biz.id,
        account_id=acc.id,
        transaction_date=date(2026, 1, 12),
        amount=Decimal("45000.00"),
        description="NEFT/RTGS ACME Corp settlement INV-450",
        transaction_type=TransactionType.INFLOW,
        category=TransactionCategory.REVENUE,
        status=TransactionStatus.POSTED
    )
    db_session.add_all([inv, tx])
    db_session.commit()

    # 1. Discover candidates
    candidates = ReconciliationService.find_candidate_matches(db_session, biz.id)
    assert len(candidates) >= 1
    match = candidates[0]
    assert match["invoice_id"] == inv.id
    assert match["transaction_id"] == tx.id
    assert match["match_type"] == "EXACT"
    assert match["confidence_score"] >= Decimal("90.00")

    # 2. Approve reconciliation
    res = ReconciliationService.approve_reconciliation(
        db=db_session,
        reconciliation_id=match["reconciliation_id"],
        business_id=biz.id,
        user_id=test_user.id
    )
    assert res["status"] == "APPROVED"

    # Verify state updates
    db_session.refresh(inv)
    db_session.refresh(tx)
    assert inv.status == InvoiceStatus.PAID
    assert inv.amount_paid == Decimal("45000.00")
    assert tx.status == TransactionStatus.RECONCILED

    # 3. Test double reconciliation prevention
    with pytest.raises(ValueError, match="already been approved"):
        ReconciliationService.approve_reconciliation(
            db=db_session,
            reconciliation_id=match["reconciliation_id"],
            business_id=biz.id,
            user_id=test_user.id
        )

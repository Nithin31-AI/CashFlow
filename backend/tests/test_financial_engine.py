from decimal import Decimal
from datetime import date
import uuid
import pytest
from app.models.business import Business
from app.models.membership import BusinessMembership, MembershipRole
from app.models.account import FinancialAccount, AccountType
from app.models.transaction import Transaction, TransactionCategory, TransactionType, TransactionStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.services.financial_service import FinancialService
from app.services.currency_service import CurrencyService

def test_decimal_account_balance_calculation(db_session, test_user):
    biz = Business(name="FinCorp", slug=f"fincorp-{uuid.uuid4().hex[:6]}", currency="INR")
    db_session.add(biz)
    db_session.flush()

    acc = FinancialAccount(
        business_id=biz.id,
        name="Main Operating Account",
        account_type=AccountType.BANK,
        opening_balance=Decimal("50000.00"),
        opening_balance_date=date(2026, 1, 1),
        currency="INR"
    )
    db_session.add(acc)
    db_session.flush()

    # Inflow of 25000.50
    tx1 = Transaction(
        business_id=biz.id,
        account_id=acc.id,
        transaction_date=date(2026, 1, 10),
        amount=Decimal("25000.50"),
        description="Client payment",
        transaction_type=TransactionType.INFLOW,
        category=TransactionCategory.REVENUE,
        status=TransactionStatus.POSTED
    )
    # Outflow of 12000.25
    tx2 = Transaction(
        business_id=biz.id,
        account_id=acc.id,
        transaction_date=date(2026, 1, 15),
        amount=Decimal("-12000.25"),
        description="Cloud infrastructure",
        transaction_type=TransactionType.OUTFLOW,
        category=TransactionCategory.SOFTWARE,
        status=TransactionStatus.POSTED
    )
    db_session.add_all([tx1, tx2])
    db_session.commit()

    bal = FinancialService.calculate_account_balance(db_session, acc.id, biz.id)
    # Expected: 50000.00 + 25000.50 - 12000.25 = 63000.25
    assert bal["current_balance"] == Decimal("63000.25")
    assert bal["total_inflows"] == Decimal("25000.50")
    assert bal["total_outflows"] == Decimal("12000.25")


def test_unpaid_invoices_not_counted_in_cash(db_session, test_user):
    biz = Business(name="AgencyX", slug=f"agencyx-{uuid.uuid4().hex[:6]}", currency="INR")
    db_session.add(biz)
    db_session.flush()

    acc = FinancialAccount(
        business_id=biz.id,
        name="Bank",
        account_type=AccountType.BANK,
        opening_balance=Decimal("10000.00"),
        currency="INR"
    )
    db_session.add(acc)
    db_session.flush()

    # Unpaid invoice of 150000.00
    inv = Invoice(
        business_id=biz.id,
        invoice_number="INV-2026-001",
        customer_name="MegaClient Ltd",
        issue_date=date(2026, 1, 5),
        due_date=date(2026, 2, 5),
        currency="INR",
        subtotal=Decimal("150000.00"),
        total_amount=Decimal("150000.00"),
        amount_paid=Decimal("0.00"),
        status=InvoiceStatus.SENT
    )
    db_session.add(inv)
    db_session.commit()

    pos = FinancialService.get_business_financial_position(db_session, biz.id)
    # Cash must strictly remain 10000.00 (Unpaid invoice must NEVER be added to liquid cash)
    assert pos["actual_cash_balance"] == Decimal("10000.00")
    assert pos["outstanding_receivables"] == Decimal("150000.00")


def test_internal_transfers_excluded_from_revenue_and_expense(db_session, test_user):
    biz = Business(name="TransferCo", slug=f"transco-{uuid.uuid4().hex[:6]}", currency="INR")
    db_session.add(biz)
    db_session.flush()

    acc_a = FinancialAccount(business_id=biz.id, name="Checking", account_type=AccountType.BANK, opening_balance=Decimal("80000.00"))
    acc_b = FinancialAccount(business_id=biz.id, name="Savings", account_type=AccountType.BANK, opening_balance=Decimal("20000.00"))
    db_session.add_all([acc_a, acc_b])
    db_session.flush()

    # Transfer 30,000 from Checking to Savings
    tx_out = Transaction(
        business_id=biz.id,
        account_id=acc_a.id,
        transaction_date=date(2026, 1, 20),
        amount=Decimal("-30000.00"),
        description="Transfer to Savings",
        category=TransactionCategory.INTERNAL_TRANSFER,
        transaction_type=TransactionType.INTERNAL_TRANSFER,
        is_internal_transfer=True,
        status=TransactionStatus.POSTED
    )
    tx_in = Transaction(
        business_id=biz.id,
        account_id=acc_b.id,
        transaction_date=date(2026, 1, 20),
        amount=Decimal("30000.00"),
        description="Transfer from Checking",
        category=TransactionCategory.INTERNAL_TRANSFER,
        transaction_type=TransactionType.INTERNAL_TRANSFER,
        is_internal_transfer=True,
        status=TransactionStatus.POSTED
    )
    db_session.add_all([tx_out, tx_in])
    db_session.commit()

    pos = FinancialService.get_business_financial_position(db_session, biz.id)
    # Total cash remains 80000 + 20000 = 100000.00
    assert pos["actual_cash_balance"] == Decimal("100000.00")
    # Revenue and expense must be 0.00 (Internal transfer must NOT register as income or expense!)
    assert pos["total_revenue"] == Decimal("0.00")
    assert pos["total_expenses"] == Decimal("0.00")


def test_multi_currency_conversion(db_session):
    # Convert 1,000 USD to INR
    res = CurrencyService.convert_amount(
        db=db_session,
        amount=Decimal("1000.00"),
        from_currency="USD",
        to_currency="INR"
    )
    assert res["is_converted"] is True
    assert res["reporting_currency"] == "INR"
    assert res["exchange_rate"] == Decimal("86.500000")
    assert res["converted_amount"] == Decimal("86500.00")
    assert res["rate_source"] == "RBI_REFERENCE"

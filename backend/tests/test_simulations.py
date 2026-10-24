from decimal import Decimal
from app.models.business import Business
from app.models.account import FinancialAccount, AccountType
from app.models.transaction import Transaction, TransactionType, TransactionCategory, TransactionStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.services.simulation_service import SimulationService

def test_monte_carlo_simulation_reproducibility_and_percentiles(db_session):
    # Setup test business
    biz = Business(name="Simulation Test Corp", slug="sim-test", currency="INR", country="IN")
    db_session.add(biz)
    db_session.flush()

    acc = FinancialAccount(
        business_id=biz.id,
        name="Operating Bank",
        account_type=AccountType.BANK,
        currency="INR",
        opening_balance=Decimal("200000.00"),
    )
    db_session.add(acc)
    db_session.flush()

    # Clear transaction inflows and outflows
    t1 = Transaction(
        business_id=biz.id,
        account_id=acc.id,
        transaction_date=acc.opening_balance_date,
        amount=Decimal("50000.00"),
        currency="INR",
        transaction_type=TransactionType.INFLOW,
        category=TransactionCategory.REVENUE,
        status=TransactionStatus.POSTED,
        description="Client payment",
    )
    t2 = Transaction(
        business_id=biz.id,
        account_id=acc.id,
        transaction_date=acc.opening_balance_date,
        amount=Decimal("-20000.00"),
        currency="INR",
        transaction_type=TransactionType.OUTFLOW,
        category=TransactionCategory.RENT,
        status=TransactionStatus.POSTED,
        description="Office rent",
    )
    db_session.add_all([t1, t2])
    db_session.commit()

    # Run 1: with seed 42
    run1 = SimulationService.run_monte_carlo(
        db=db_session,
        business_id=biz.id,
        horizon_days=30,
        num_paths=500,
        seed=42,
    )

    # Run 2: with identical seed 42
    run2 = SimulationService.run_monte_carlo(
        db=db_session,
        business_id=biz.id,
        horizon_days=30,
        num_paths=500,
        seed=42,
    )

    # Assert exact reproducibility with identical seed
    assert run1.p10_ending_cash == run2.p10_ending_cash
    assert run1.p50_ending_cash == run2.p50_ending_cash
    assert run1.p90_ending_cash == run2.p90_ending_cash
    assert run1.reserve_breach_probability == run2.reserve_breach_probability

    # Assert mathematical hierarchy: p10 <= p50 <= p90
    assert float(run1.p10_ending_cash) <= float(run1.p50_ending_cash)
    assert float(run1.p50_ending_cash) <= float(run1.p90_ending_cash)
    assert run1.num_paths == 500
    assert len(run1.percentile_paths) == 31  # day 0 to 30
    assert run1.assumptions["minimum_cash_reserve"] >= 0.0

def test_monte_carlo_with_payment_delay_and_invoices(db_session):
    biz = Business(name="Invoicing Test Corp", slug="inv-sim-test", currency="INR", country="IN")
    db_session.add(biz)
    db_session.flush()

    acc = FinancialAccount(
        business_id=biz.id,
        name="Operating Bank",
        account_type=AccountType.BANK,
        currency="INR",
        opening_balance=Decimal("150000.00"),
    )
    db_session.add(acc)
    db_session.flush()

    # Pending customer invoice
    inv = Invoice(
        business_id=biz.id,
        customer_name="Key Client Ltd",
        invoice_number="INV-SIM-001",
        issue_date=acc.opening_balance_date,
        due_date=acc.opening_balance_date,
        currency="INR",
        subtotal=Decimal("80000.00"),
        total_amount=Decimal("80000.00"),
        amount_paid=Decimal("0.00"),
        status=InvoiceStatus.SENT,
    )
    db_session.add(inv)
    db_session.commit()

    run = SimulationService.run_monte_carlo(
        db=db_session,
        business_id=biz.id,
        horizon_days=30,
        num_paths=200,
        seed=101,
        custom_delay_days=15,
        collection_probability=0.85,
    )

    assert run.assumptions["scheduled_invoices_count"] == 1
    assert run.assumptions["total_pending_receivables"] == 80000.0
    assert float(run.p50_ending_cash) > 100000.0

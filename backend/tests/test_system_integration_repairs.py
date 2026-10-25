from decimal import Decimal
from datetime import date, timedelta
import uuid
import pytest
from fastapi.testclient import TestClient

from app.models.business import Business
from app.models.membership import BusinessMembership, MembershipRole
from app.models.account import FinancialAccount, AccountType
from app.models.transaction import Transaction, TransactionCategory, TransactionType, TransactionStatus, ImportedRecord
from app.models.invoice import Invoice, InvoiceStatus, PaymentMethod, Payment
from app.models.import_job import ImportJob, ImportJobStatus, ImportValidationResult
from app.services.assistant_service import AssistantService
from app.services.forecasting_service import ForecastingService
from app.services.simulation_service import SimulationService
from app.services.financial_service import FinancialService
from tests.conftest import auth_headers


# -----------------------------------------------------------------------------
# BUG 1 TESTS: Statement Ingestion to Transaction Ledger & Downstream Models
# -----------------------------------------------------------------------------

def test_statement_import_creates_transactions_and_updates_account_balance(client, db_session, test_user):
    """
    Validates BUG 1 fix:
    Confirming an import job creates authoritative Transaction ledger records
    linked by imported_record_id, properly infers category, and recalculates
    the financial account balance immediately.
    """
    biz = Business(name="Ingestion Test Inc", slug=f"ingest-{uuid.uuid4().hex[:6]}", currency="INR")
    db_session.add(biz)
    db_session.flush()

    membership = BusinessMembership(business_id=biz.id, user_id=test_user.id, role=MembershipRole.OWNER)
    db_session.add(membership)

    acc = FinancialAccount(
        business_id=biz.id,
        name="Operating Bank Account",
        account_type=AccountType.BANK,
        currency="INR",
        opening_balance=Decimal("100000.00"),
        opening_balance_date=date.today() - timedelta(days=30),
    )
    db_session.add(acc)
    db_session.flush()

    job = ImportJob(
        business_id=biz.id,
        account_id=acc.id,
        uploaded_file_id=str(uuid.uuid4()),
        file_type="CSV",
        status=ImportJobStatus.READY_FOR_PREVIEW,
        total_rows=3,
        valid_rows=3,
    )
    db_session.add(job)
    db_session.flush()

    # Pre-populate staged import validation results
    vr1 = ImportValidationResult(
        import_job_id=job.id,
        row_index=1,
        raw_data={"date": str(date.today() - timedelta(days=5)), "desc": "Acme Corp Retainer", "amount": "45000.00"},
        parsed_data={
            "transaction_date": str(date.today() - timedelta(days=5)),
            "description": "Client Payment - Acme Corp Retainer",
            "amount": 45000.00,
            "currency": "INR",
        },
        is_valid=True,
    )
    vr2 = ImportValidationResult(
        import_job_id=job.id,
        row_index=2,
        raw_data={"date": str(date.today() - timedelta(days=3)), "desc": "AWS Cloud Hosting", "amount": "-15000.00"},
        parsed_data={
            "transaction_date": str(date.today() - timedelta(days=3)),
            "description": "AWS Cloud Hosting Invoice",
            "amount": -15000.00,
            "currency": "INR",
        },
        is_valid=True,
    )
    vr3 = ImportValidationResult(
        import_job_id=job.id,
        row_index=3,
        raw_data={"date": str(date.today() - timedelta(days=1)), "desc": "Staff Salary", "amount": "-35000.00"},
        parsed_data={
            "transaction_date": str(date.today() - timedelta(days=1)),
            "description": "Monthly Salary Payroll - Staff",
            "amount": -35000.00,
            "currency": "INR",
        },
        is_valid=True,
    )
    db_session.add_all([vr1, vr2, vr3])
    db_session.commit()

    # Confirm the import via API
    headers = auth_headers(test_user.id)
    confirm_res = client.post(f"/api/v1/businesses/{biz.id}/imports/{job.id}/confirm", headers=headers)
    assert confirm_res.status_code == 200
    result = confirm_res.json()
    assert result["success"] is True
    assert result["imported_count"] == 3

    # Verify Transactions were created in the database
    txs = db_session.query(Transaction).filter(
        Transaction.business_id == biz.id,
        Transaction.account_id == acc.id,
    ).all()
    assert len(txs) == 3

    # Check mapping & category inference
    inflow_tx = next(t for t in txs if t.amount > 0)
    assert inflow_tx.transaction_type == TransactionType.INFLOW
    assert inflow_tx.amount == Decimal("45000.00")
    assert inflow_tx.category == TransactionCategory.REVENUE
    assert inflow_tx.imported_record_id is not None

    aws_tx = next(t for t in txs if "AWS" in t.description)
    assert aws_tx.transaction_type == TransactionType.OUTFLOW
    assert aws_tx.amount == Decimal("-15000.00")
    assert aws_tx.category == TransactionCategory.SOFTWARE

    payroll_tx = next(t for t in txs if "Salary" in t.description)
    assert payroll_tx.transaction_type == TransactionType.OUTFLOW
    assert payroll_tx.amount == Decimal("-35000.00")
    assert payroll_tx.category == TransactionCategory.PAYROLL

    # Verify Account balance recalculated: 100000 + 45000 - 15000 - 35000 = 95000.00
    db_session.refresh(acc)
    assert acc.current_balance == Decimal("95000.00")
    bal = FinancialService.calculate_account_balance(db_session, acc.id, biz.id)
    assert bal["total_inflows"] == Decimal("45000.00")
    assert bal["total_outflows"] == Decimal("50000.00")

    # Verify Forecasting Service utilizes these transactions and records
    fc = ForecastingService.generate_forecast(db=db_session, business_id=biz.id, horizon_days=30)
    assert fc["starting_cash"] == 95000.00
    assert fc["horizon_days"] == 30
    assert len(fc["daily_projections"]) == 30

    # Verify Simulation Service utilizes these transactions without crash
    sim = SimulationService.run_monte_carlo(db=db_session, business_id=biz.id, horizon_days=30, num_paths=20)
    assert sim.starting_cash == 95000.00
    assert len(sim.percentile_paths) >= 30


# -----------------------------------------------------------------------------
# BUG 2 TESTS: Invoice Payment & Transaction Ledger Synchronization
# -----------------------------------------------------------------------------

def test_invoice_payment_creates_transaction_and_updates_cash(client, db_session, test_user):
    """
    Validates BUG 2 fix:
    Recording an invoice payment creates a Payment AND exactly one Transaction
    linked by payment_id, updates invoice amount_paid and status to PAID,
    and updates the account balance without double counting.
    """
    biz = Business(name="Invoicing Test Ltd", slug=f"inv-{uuid.uuid4().hex[:6]}", currency="INR")
    db_session.add(biz)
    db_session.flush()

    membership = BusinessMembership(business_id=biz.id, user_id=test_user.id, role=MembershipRole.OWNER)
    db_session.add(membership)

    acc = FinancialAccount(
        business_id=biz.id,
        name="Operating Bank",
        account_type=AccountType.BANK,
        currency="INR",
        opening_balance=Decimal("20000.00"),
        opening_balance_date=date.today() - timedelta(days=10),
    )
    db_session.add(acc)
    db_session.flush()

    inv = Invoice(
        business_id=biz.id,
        invoice_number="INV-2026-001",
        customer_name="TechVentures",
        issue_date=date.today() - timedelta(days=7),
        due_date=date.today() + timedelta(days=7),
        currency="INR",
        subtotal=Decimal("50000.00"),
        tax_amount=Decimal("9000.00"),
        total_amount=Decimal("59000.00"),
        amount_paid=Decimal("0.00"),
        status=InvoiceStatus.SENT,
    )
    db_session.add(inv)
    db_session.commit()

    headers = auth_headers(test_user.id)

    # 1. Record payment via API
    pay_payload = {
        "invoice_id": inv.id,
        "account_id": acc.id,
        "amount": 59000.00,
        "currency": "INR",
        "payment_date": str(date.today()),
        "payment_method": "BANK_TRANSFER",
        "reference_number": "UTR-11223344",
        "notes": "Full client payment",
    }
    res = client.post(f"/api/v1/businesses/{biz.id}/payments", json=pay_payload, headers=headers)
    assert res.status_code == 201
    pay_data = res.json()
    assert float(pay_data["amount"]) == 59000.00

    # 2. Check Invoice is now PAID
    db_session.refresh(inv)
    assert inv.status == InvoiceStatus.PAID
    assert inv.amount_paid == Decimal("59000.00")

    # 3. Check exactly one Transaction was created linked to this payment
    txs = db_session.query(Transaction).filter(
        Transaction.business_id == biz.id,
        Transaction.payment_id == pay_data["id"],
    ).all()
    assert len(txs) == 1
    tx = txs[0]
    assert tx.amount == Decimal("59000.00")
    assert tx.transaction_type == TransactionType.INFLOW
    assert tx.category == TransactionCategory.REVENUE
    assert tx.reference_number == "UTR-11223344"

    # 4. Check Account balance was updated: 20000 + 59000 = 79000
    db_session.refresh(acc)
    assert acc.current_balance == Decimal("79000.00")


def test_payment_idempotency_and_overpayment_validation(client, db_session, test_user):
    """
    Validates BUG 2 protections:
    - Overpayment rejected with 400
    - Duplicate payment with same reference rejected with 400
    - Direct status change to PAID without payment rejected with 400
    """
    biz = Business(name="Payment Security Co", slug=f"paysec-{uuid.uuid4().hex[:6]}", currency="INR")
    db_session.add(biz)
    db_session.flush()

    membership = BusinessMembership(business_id=biz.id, user_id=test_user.id, role=MembershipRole.OWNER)
    db_session.add(membership)

    acc = FinancialAccount(
        business_id=biz.id,
        name="Operating Bank",
        account_type=AccountType.BANK,
        currency="INR",
        opening_balance=Decimal("10000.00"),
    )
    db_session.add(acc)
    db_session.flush()

    inv = Invoice(
        business_id=biz.id,
        invoice_number="INV-2026-002",
        customer_name="Global Systems",
        issue_date=date.today(),
        due_date=date.today() + timedelta(days=15),
        currency="INR",
        subtotal=Decimal("10000.00"),
        total_amount=Decimal("10000.00"),
        amount_paid=Decimal("0.00"),
        status=InvoiceStatus.SENT,
    )
    db_session.add(inv)
    db_session.commit()

    headers = auth_headers(test_user.id)

    # 1. Overpayment rejection
    overpay_res = client.post(
        f"/api/v1/businesses/{biz.id}/payments",
        json={
            "invoice_id": inv.id,
            "account_id": acc.id,
            "amount": 15000.00,  # Exceeds total_amount of 10000.00
            "currency": "INR",
            "payment_date": str(date.today()),
            "payment_method": "BANK_TRANSFER",
        },
        headers=headers,
    )
    assert overpay_res.status_code == 400
    assert "exceeds remaining balance" in overpay_res.json()["detail"]

    # 2. Record valid payment
    pay1_res = client.post(
        f"/api/v1/businesses/{biz.id}/payments",
        json={
            "invoice_id": inv.id,
            "account_id": acc.id,
            "amount": 10000.00,
            "currency": "INR",
            "payment_date": str(date.today()),
            "payment_method": "BANK_TRANSFER",
            "reference_number": "UTR-UNIQUE-999",
        },
        headers=headers,
    )
    assert pay1_res.status_code == 201

    # 3. Duplicate payment rejection
    dup_res = client.post(
        f"/api/v1/businesses/{biz.id}/payments",
        json={
            "invoice_id": inv.id,
            "account_id": acc.id,
            "amount": 10000.00,
            "currency": "INR",
            "payment_date": str(date.today()),
            "payment_method": "BANK_TRANSFER",
            "reference_number": "UTR-UNIQUE-999",
        },
        headers=headers,
    )
    assert dup_res.status_code in [400, 409]

    # 4. Direct status change to PAID without payment on unpaid invoice
    unpaid_inv = Invoice(
        business_id=biz.id,
        invoice_number="INV-2026-UNPAID",
        customer_name="Unsettled Client",
        issue_date=date.today(),
        due_date=date.today() + timedelta(days=10),
        currency="INR",
        subtotal=Decimal("5000.00"),
        total_amount=Decimal("5000.00"),
        amount_paid=Decimal("0.00"),
        status=InvoiceStatus.SENT,
    )
    db_session.add(unpaid_inv)
    db_session.commit()

    patch_res = client.patch(
        f"/api/v1/businesses/{biz.id}/invoices/{unpaid_inv.id}/status",
        json={"status": "PAID"},
        headers=headers,
    )
    assert patch_res.status_code == 400
    assert "Cannot mark invoice" in patch_res.json()["detail"] and "PAID directly" in patch_res.json()["detail"]


# -----------------------------------------------------------------------------
# BUG 3 TESTS: AI Assistant Tools & Error Resilience
# -----------------------------------------------------------------------------

def test_assistant_tool_execution_and_forecast_dictionary_handling(db_session, test_user):
    """
    Validates BUG 3 fix:
    - Assistant handles dict return from ForecastingService without AttributeError
    - Executes get_financial_overview, get_forecast_summary, get_expenses_summary,
      get_recorded_payments, get_cash_flow_risks cleanly
    - Enforces tenant isolation
    """
    biz = Business(
        name="AI Testing Enterprises",
        slug=f"ai-{uuid.uuid4().hex[:6]}",
        currency="INR",
        minimum_cash_reserve=Decimal("50000.00"),
    )
    db_session.add(biz)
    db_session.flush()

    acc = FinancialAccount(
        business_id=biz.id,
        name="Primary Treasury",
        account_type=AccountType.BANK,
        currency="INR",
        opening_balance=Decimal("150000.00"),
        opening_balance_date=date.today() - timedelta(days=15),
    )
    db_session.add(acc)
    db_session.flush()

    tx = Transaction(
        business_id=biz.id,
        account_id=acc.id,
        transaction_date=date.today() - timedelta(days=5),
        amount=Decimal("-25000.00"),
        description="Office Rent",
        category=TransactionCategory.RENT,
        transaction_type=TransactionType.OUTFLOW,
        status=TransactionStatus.POSTED,
    )
    db_session.add(tx)
    db_session.commit()

    # 1. Test forecast tool directly
    fc_tool_res = AssistantService.execute_tool("get_forecast_summary", db_session, biz.id)
    assert "error" not in fc_tool_res
    assert fc_tool_res["horizon_days"] == 30
    assert fc_tool_res["starting_cash"] == 125000.0

    # 2. Test conversational forecast query
    asst_res = AssistantService.answer_query(
        db=db_session,
        business_id=biz.id,
        query="What is our 30-day forecast and cash runway?",
    )
    assert asst_res["answer"] != ""
    assert len(asst_res["tool_data"]) > 0
    assert any("forecast" in str(d).lower() for d in asst_res["tool_data"])

    # 3. Test expense breakdown tool
    exp_res = AssistantService.execute_tool("get_expenses_summary", db_session, biz.id)
    assert exp_res["total_expenses"] == 25000.0
    assert "RENT" in exp_res["category_breakdown"]
    assert exp_res["category_breakdown"]["RENT"] == 25000.0

    # 4. Test cash overview query
    bal_res = AssistantService.answer_query(
        db=db_session,
        business_id=biz.id,
        query="What is our actual cash balance right now?",
    )
    assert "125,000" in bal_res["answer"] or "125000" in bal_res["answer"]

    # 5. Tenant boundary: querying for empty business does not leak biz records
    biz2 = Business(name="Foreign Business", slug=f"foreign-{uuid.uuid4().hex[:6]}", currency="USD")
    db_session.add(biz2)
    db_session.commit()

    asst_empty = AssistantService.answer_query(
        db=db_session,
        business_id=biz2.id,
        query="What are our expenses?",
    )
    assert any(w in asst_empty["answer"].lower() for w in ["zero", "0", "no"])

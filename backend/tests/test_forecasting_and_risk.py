from decimal import Decimal
from datetime import date, datetime, timedelta, timezone
import uuid
import pytest
from app.models.business import Business
from app.models.account import FinancialAccount, AccountType
from app.models.transaction import Transaction, TransactionType, TransactionCategory, TransactionStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.services.forecasting_service import ForecastingService
from app.services.risk_service import RiskService

def test_multi_horizon_forecasting_and_confidence_bounds(db_session, test_user):
    biz = Business(name="PredictCo", slug=f"pred-{uuid.uuid4().hex[:6]}", currency="INR")
    db_session.add(biz)
    db_session.flush()

    acc = FinancialAccount(
        business_id=biz.id,
        name="Operating",
        account_type=AccountType.BANK,
        opening_balance=Decimal("200000.00")
    )
    db_session.add(acc)
    db_session.flush()

    # Outflows in last 30 days of 60,000 (avg 2,000/day)
    today = datetime.now(timezone.utc).date()
    for i in range(1, 4):
        tx = Transaction(
            business_id=biz.id,
            account_id=acc.id,
            transaction_date=today - timedelta(days=i * 5),
            amount=Decimal("-20000.00"),
            description=f"Operational cost {i}",
            category=TransactionCategory.SOFTWARE,
            transaction_type=TransactionType.OUTFLOW,
            status=TransactionStatus.POSTED
        )
        db_session.add(tx)

    # Invoices scheduled in next 20 days
    inv = Invoice(
        business_id=biz.id,
        invoice_number="INV-FUTURE-01",
        customer_name="Client Alpha",
        issue_date=today,
        due_date=today + timedelta(days=15),
        subtotal=Decimal("80000.00"),
        total_amount=Decimal("80000.00"),
        status=InvoiceStatus.SENT
    )
    db_session.add(inv)
    db_session.commit()

    # 1. Test 30-day horizon
    forecast_30 = ForecastingService.generate_forecast(db_session, biz.id, horizon_days=30)
    assert forecast_30["horizon_days"] == 30
    assert len(forecast_30["daily_projections"]) == 30
    assert forecast_30["starting_cash"] == 140000.00
    # Confidence upper bound must exceed confidence lower bound
    assert forecast_30["confidence_upper"] > forecast_30["confidence_lower"]

    # 2. Test 90-day horizon
    forecast_90 = ForecastingService.generate_forecast(db_session, biz.id, horizon_days=90)
    assert forecast_90["horizon_days"] == 90
    assert len(forecast_90["daily_projections"]) == 90


def test_cash_shortage_risk_detection(db_session, test_user):
    biz = Business(
        name="RiskCorp",
        slug=f"risk-{uuid.uuid4().hex[:6]}",
        currency="INR",
        minimum_cash_reserve=Decimal("100000.00")
    )
    db_session.add(biz)
    db_session.flush()

    # Projections where cash dips to 30,000 on day 10 (shortfall = 70,000 below 100,000 reserve)
    projections = [
        {"date": "2026-02-01", "projected_cash": 120000.0},
        {"date": "2026-02-05", "projected_cash": 80000.0},
        {"date": "2026-02-10", "projected_cash": 30000.0},
    ]

    risks = RiskService.evaluate_cash_shortage_risk(
        db=db_session,
        business_id=biz.id,
        projections=projections,
        minimum_reserve=biz.minimum_cash_reserve
    )

    assert len(risks) == 1
    shortage_risk = risks[0]
    assert shortage_risk["risk_type"] == "CASH_SHORTAGE"
    assert shortage_risk["severity"] in ["HIGH", "CRITICAL"]
    assert shortage_risk["estimated_shortfall"] == 70000.0
    assert "safety buffer" in shortage_risk["description"]

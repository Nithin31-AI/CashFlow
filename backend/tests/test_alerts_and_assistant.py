from decimal import Decimal
from app.models.business import Business
from app.models.account import FinancialAccount, AccountType
from app.models.invoice import Invoice, InvoiceStatus
from app.models.alert import AlertCategory, AlertSeverity
from app.services.alert_service import AlertService
from app.services.assistant_service import AssistantService

def test_alert_rules_evaluation_and_duplicate_suppression(db_session):
    biz = Business(
        name="Alerts Test Agency",
        slug="alert-test",
        currency="INR",
        country="IN",
        minimum_cash_reserve=Decimal("100000.00"),
    )
    db_session.add(biz)
    db_session.flush()

    acc = FinancialAccount(
        business_id=biz.id,
        name="Operating Bank",
        account_type=AccountType.BANK,
        currency="INR",
        opening_balance=Decimal("60000.00"),  # Breaches 100k reserve
    )
    db_session.add(acc)
    db_session.commit()

    # Initial evaluation: should trigger reserve breach alert
    triggered1 = AlertService.evaluate_rules_and_trigger(db=db_session, business_id=biz.id)
    assert len(triggered1) >= 1
    assert any(a.category == AlertCategory.RESERVE_BREACH.value for a in triggered1)

    # Immediate second evaluation: must be suppressed by 24h suppression window
    triggered2 = AlertService.evaluate_rules_and_trigger(db=db_session, business_id=biz.id)
    assert len(triggered2) == 0  # Duplicate suppressed!

def test_conversational_assistant_grounded_tool_execution(db_session):
    biz = Business(
        name="Assistant Test Labs",
        slug="asst-test",
        currency="INR",
        country="IN",
        minimum_cash_reserve=Decimal("75000.00"),
    )
    db_session.add(biz)
    db_session.flush()

    acc = FinancialAccount(
        business_id=biz.id,
        name="Primary Current",
        account_type=AccountType.BANK,
        currency="INR",
        opening_balance=Decimal("125000.00"),
    )
    db_session.add(acc)
    db_session.flush()

    # Invoice
    inv = Invoice(
        business_id=biz.id,
        customer_name="Global Tech Corp",
        invoice_number="INV-ASST-01",
        issue_date=acc.opening_balance_date,
        due_date=acc.opening_balance_date,
        currency="INR",
        subtotal=Decimal("45000.00"),
        total_amount=Decimal("45000.00"),
        amount_paid=Decimal("0.00"),
        status=InvoiceStatus.OVERDUE,
    )
    db_session.add(inv)
    db_session.commit()

    # Query 1: Cash balance
    resp_cash = AssistantService.answer_query(db=db_session, business_id=biz.id, query="What is our current cash balance?")
    assert "₹125,000.00" in resp_cash["answer"]
    assert "Verified Cleared Bank Ledger" in resp_cash["citations"]

    # Query 2: Overdue invoices
    resp_inv = AssistantService.answer_query(db=db_session, business_id=biz.id, query="Which customer invoices are overdue?")
    assert "₹45,000.00" in resp_inv["answer"]
    assert "Accounts Receivable Ledger" in resp_inv["citations"]

def test_alert_events_api_boundary_and_null_category_resilience(client, db_session, test_user):
    from tests.conftest import auth_headers
    from app.models.membership import BusinessMembership, MembershipRole
    from app.models.alert import AlertEvent, AlertSeverity

    biz = Business(
        name="Resilience Test Corp",
        slug="resilience-corp",
        currency="INR",
        country="IN",
    )
    db_session.add(biz)
    db_session.flush()

    membership = BusinessMembership(
        user_id=test_user.id,
        business_id=biz.id,
        role=MembershipRole.OWNER,
    )
    db_session.add(membership)
    db_session.commit()

    headers = auth_headers(test_user.id)

    from datetime import datetime, timezone
    from app.api.v1.alerts import AlertEventResponse

    # 1. Test AlertEventResponse validator: category=None is coerced to "GENERAL"
    coerced = AlertEventResponse.model_validate({
        "id": "mock-id-1",
        "business_id": biz.id,
        "title": "Untyped Alert",
        "message": "Testing null category handling.",
        "category": None,
        "severity": AlertSeverity.WARNING,
        "created_at": datetime.now(timezone.utc),
    })
    assert coerced.category == "GENERAL"
    assert coerced.category.replace("_", " ") == "GENERAL"

    # 2. Insert an alert event with omitted category (model default="GENERAL")
    legacy_ev = AlertEvent(
        business_id=biz.id,
        title="Legacy Uncategorized Alert",
        message="System detected an untyped liquidity variance.",
        severity=AlertSeverity.WARNING,
        financial_evidence={"variance": 12500},
    )
    db_session.add(legacy_ev)
    db_session.commit()
    db_session.refresh(legacy_ev)

    # 3. Call GET /{business_id}/alerts/events
    res = client.get(f"/api/v1/businesses/{biz.id}/alerts/events", headers=headers)
    assert res.status_code == 200
    events = res.json()
    assert len(events) >= 1
    target = next((e for e in events if e["id"] == legacy_ev.id), None)
    assert target is not None
    assert target["category"] == "GENERAL"
    assert target["severity"] == "WARNING"

    # 4. Acknowledge alert
    ack_res = client.post(f"/api/v1/businesses/{biz.id}/alerts/events/{legacy_ev.id}/acknowledge", headers=headers)
    assert ack_res.status_code == 200
    assert ack_res.json()["is_acknowledged"] is True

    # 5. Resolve alert
    res_res = client.post(f"/api/v1/businesses/{biz.id}/alerts/events/{legacy_ev.id}/resolve", headers=headers)
    assert res_res.status_code == 200
    assert res_res.json()["is_resolved"] is True

    # 5. Create valid alert rule
    rule_res = client.post(f"/api/v1/businesses/{biz.id}/alerts/rules", json={
        "name": "Overdue Warning",
        "category": "OVERDUE_INVOICE",
        "threshold_value": 50000,
        "severity": "WARNING",
        "suppression_window_hours": 24,
    }, headers=headers)
    assert rule_res.status_code == 201
    assert rule_res.json()["category"] == "OVERDUE_INVOICE"


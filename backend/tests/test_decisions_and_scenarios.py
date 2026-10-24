from decimal import Decimal
from app.models.business import Business
from app.models.account import FinancialAccount, AccountType
from app.models.invoice import Invoice, InvoiceStatus
from app.models.transaction import Transaction, TransactionType, TransactionCategory, TransactionStatus
from app.models.goal import GoalType, GoalStatus
from app.services.decision_service import DecisionService

def test_goals_and_constrained_optimisation(db_session):
    biz = Business(
        name="Decision Test Studio",
        slug="dec-test",
        currency="INR",
        country="IN",
        minimum_cash_reserve=Decimal("50000.00"),
    )
    db_session.add(biz)
    db_session.flush()

    acc = FinancialAccount(
        business_id=biz.id,
        name="Main Account",
        account_type=AccountType.BANK,
        currency="INR",
        opening_balance=Decimal("40000.00"),  # Below reserve (shortfall of 10,000)
    )
    db_session.add(acc)
    db_session.flush()

    # Overdue invoice of 30,000
    inv = Invoice(
        business_id=biz.id,
        customer_name="Acme Client",
        invoice_number="INV-DEC-1",
        issue_date=acc.opening_balance_date,
        due_date=acc.opening_balance_date,
        currency="INR",
        subtotal=Decimal("30000.00"),
        total_amount=Decimal("30000.00"),
        amount_paid=Decimal("0.00"),
        status=InvoiceStatus.OVERDUE,
    )
    db_session.add(inv)
    db_session.commit()

    # Set hard constraint goal: Minimum Reserve 60,000
    goal = DecisionService.create_or_update_goal(
        db=db_session,
        business_id=biz.id,
        name="Maintain 60k Buffer",
        goal_type=GoalType.MINIMUM_RESERVE,
        target_amount=Decimal("60000.00"),
        is_hard_constraint=True,
    )
    assert goal.status == GoalStatus.ACTIVE
    assert goal.is_hard_constraint is True

    # Run decision optimization
    plan = DecisionService.run_decision_optimisation(db=db_session, business_id=biz.id)

    # Invoices (30,000) exceed shortfall (60,000 - 40,000 = 20,000), making plan feasible
    assert plan.status.value in ["FEASIBLE", "PARTIALLY_FEASIBLE"]
    assert len(plan.recommended_actions) >= 1
    assert any(a["action_type"] == "INVOICE_FOLLOWUP" for a in plan.recommended_actions)
    assert plan.objective_value >= Decimal("30000.00")

def test_scenario_creation_and_comparison(db_session):
    biz = Business(
        name="Scenario Test Corp",
        slug="scen-test",
        currency="INR",
        country="IN",
        minimum_cash_reserve=Decimal("50000.00"),
    )
    db_session.add(biz)
    db_session.flush()

    acc = FinancialAccount(
        business_id=biz.id,
        name="Operating Bank",
        account_type=AccountType.BANK,
        currency="INR",
        opening_balance=Decimal("100000.00"),
    )
    db_session.add(acc)
    db_session.commit()

    # Baseline scenario (0 delay, 0 capex)
    s_base = DecisionService.evaluate_scenario(
        db=db_session,
        business_id=biz.id,
        name="Baseline",
        receivable_delay_days=0,
        one_off_capex=0.0,
    )

    # Stressed scenario (30-day delay, 40,000 CapEx)
    s_stress = DecisionService.evaluate_scenario(
        db=db_session,
        business_id=biz.id,
        name="Stressed Scenario",
        receivable_delay_days=30,
        one_off_capex=40000.0,
    )

    # Assert stressed ending cash is strictly lower than baseline
    assert float(s_stress.projected_ending_cash) < float(s_base.projected_ending_cash)
    assert s_stress.parameters["one_off_capex"] == 40000.0
    assert s_stress.parameters["receivable_delay_days"] == 30

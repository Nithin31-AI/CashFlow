import os
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import app.models
from app.db.session import SessionLocal, engine, Base
from app.models.business import Business
from app.models.user import User
from app.models.membership import BusinessMembership, MembershipRole
from app.models.account import FinancialAccount, AccountType
from app.models.invoice import Invoice, InvoiceStatus
from app.models.transaction import Transaction, TransactionType, TransactionCategory, TransactionStatus
from app.models.alert import AlertRule, AlertEvent, AlertCategory, AlertSeverity
from app.models.forecast import RiskAssessment, RiskType, RiskSeverity, RiskStatus
from app.models.goal import FinancialGoal, GoalType, GoalStatus
from app.services.financial_service import FinancialService
from app.services.forecasting_service import ForecastingService
from app.services.simulation_service import SimulationService
from app.services.decision_service import DecisionService
from app.services.alert_service import AlertService

# Standard verified bcrypt hash for 'Password123!'
BCRYPT_HASH = "$2b$12$rqNFvHL9duioB/Xs5qD1pe1Hry4ft65VoYBG30Udl1ozhuxu1GZs2"
BUSINESS_ID = "11111111-1111-1111-1111-111111111111"

def seed_acme_dataset():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        print("=" * 60)
        print("[*] Seeding Acme Consulting Tech Ltd Synthetic Test Dataset")
        print("=" * 60)

        # 1. Multi-Tenant Business
        business = db.query(Business).filter(Business.id == BUSINESS_ID).first()
        if not business:
            business = Business(
                id=BUSINESS_ID,
                name="Acme Consulting Tech Ltd",
                slug="acme-consulting-tech-ltd",
                currency="INR",
                country="IN",
                timezone="Asia/Kolkata",
                minimum_cash_reserve=Decimal("500000.00"),
            )
            db.add(business)
            print("  [+] Created Business: Acme Consulting Tech Ltd (INR)")
        else:
            business.name = "Acme Consulting Tech Ltd"
            business.minimum_cash_reserve = Decimal("500000.00")
            print("  [*] Updated Business: Acme Consulting Tech Ltd")

        db.commit()

        # 2. Team Users
        users_data = [
            ("user-owner-001", "owner@acme.com", "Alice Owner", MembershipRole.OWNER),
            ("user-fin-002", "finance@acme.com", "Bob Finance", MembershipRole.FINANCE_MANAGER),
            ("user-acc-003", "acct@acme.com", "Charlie Acct", MembershipRole.ACCOUNTANT),
            ("user-view-004", "viewer@acme.com", "David Viewer", MembershipRole.VIEWER),
        ]

        for u_id, email, name, role in users_data:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(
                    id=u_id,
                    email=email,
                    full_name=name,
                    hashed_password=BCRYPT_HASH,
                    is_active=True,
                )
                db.add(user)
                db.flush()
                print(f"  [+] Created User: {name} <{email}>")
            
            # Membership
            mem = db.query(BusinessMembership).filter(
                BusinessMembership.business_id == BUSINESS_ID,
                BusinessMembership.user_id == user.id,
            ).first()
            if not mem:
                mem = BusinessMembership(
                    id=f"mem-{user.id[:30]}",
                    business_id=BUSINESS_ID,
                    user_id=user.id,
                    role=role,
                )
                db.add(mem)
                print(f"  [+] Linked Membership: {name} -> {role.value}")

        # Link any existing local users (e.g. fakeed@gmail.com, docker_test_user@example.com) as OWNER
        existing_extra_users = db.query(User).filter(
            User.email.in_(["fakeed@gmail.com", "docker_test_user@example.com"])
        ).all()
        for eu in existing_extra_users:
            emem = db.query(BusinessMembership).filter(
                BusinessMembership.business_id == BUSINESS_ID,
                BusinessMembership.user_id == eu.id,
            ).first()
            if not emem:
                emem = BusinessMembership(
                    id=f"mem-{eu.id[:30]}",
                    business_id=BUSINESS_ID,
                    user_id=eu.id,
                    role=MembershipRole.OWNER,
                )
                db.add(emem)
                print(f"  [+] Linked Active Session User: {eu.email} as OWNER")

        db.commit()

        # 3. Bank Accounts (financial_accounts)
        # HDFC Operating Account: Opening 250,000 -> Target Current 845,000
        acc_op = db.query(FinancialAccount).filter(FinancialAccount.id == "acc-op-001").first()
        if not acc_op:
            acc_op = FinancialAccount(
                id="acc-op-001",
                business_id=BUSINESS_ID,
                name="HDFC Operating Account",
                account_type=AccountType.BANK,
                account_number_mask="•••• 4201",
                currency="INR",
                institution_name="HDFC Bank",
                opening_balance=Decimal("250000.00"),
                opening_balance_date=date(2026, 9, 1),
                is_active=True,
            )
            db.add(acc_op)
            print("  [+] Created Account: HDFC Operating Account (Opening INR 250,000)")

        # ICICI Reserve Account: Opening 500,000 -> Target Current 1,200,000
        acc_sav = db.query(FinancialAccount).filter(FinancialAccount.id == "acc-sav-002").first()
        if not acc_sav:
            acc_sav = FinancialAccount(
                id="acc-sav-002",
                business_id=BUSINESS_ID,
                name="ICICI Reserve Account",
                account_type=AccountType.BANK,
                account_number_mask="•••• 9902",
                currency="INR",
                institution_name="ICICI Bank",
                opening_balance=Decimal("500000.00"),
                opening_balance_date=date(2026, 9, 1),
                is_active=True,
            )
            db.add(acc_sav)
            print("  [+] Created Account: ICICI Reserve Account (Opening INR 500,000)")

        db.commit()

        # 4. Invoices & Receivables
        invoices_data = [
            (
                "inv-2026-001",
                "INV-2026-101",
                "Client B",
                "billing@clientb.com",
                Decimal("250000.00"),
                Decimal("0.00"),
                InvoiceStatus.OVERDUE,
                date(2026, 9, 1),
                date(2026, 9, 6),
                14,
                "Client milestone billing - payment delayed pending approval",
            ),
            (
                "inv-2026-002",
                "INV-2026-102",
                "Enterprise Client Alpha",
                "ap@clientalpha.com",
                Decimal("450000.00"),
                Decimal("0.00"),
                InvoiceStatus.SENT,
                date(2026, 9, 15),
                date(2026, 10, 15),
                3,
                "Q3 Retainer consulting services milestone",
            ),
            (
                "inv-2026-003",
                "INV-2026-103",
                "Global Digital Corp",
                "finance@globaldigital.com",
                Decimal("320000.00"),
                Decimal("320000.00"),
                InvoiceStatus.PAID,
                date(2026, 8, 15),
                date(2026, 9, 15),
                0,
                "Completed cloud infrastructure audit",
            ),
        ]

        for i_id, num, cust, email, tot, paid, status, iss, due, delay, notes in invoices_data:
            inv = db.query(Invoice).filter(Invoice.id == i_id).first()
            if not inv:
                inv = Invoice(
                    id=i_id,
                    business_id=BUSINESS_ID,
                    invoice_number=num,
                    customer_name=cust,
                    customer_email=email,
                    subtotal=tot,
                    tax_amount=Decimal("0.00"),
                    total_amount=tot,
                    amount_paid=paid,
                    status=status,
                    issue_date=iss,
                    due_date=due,
                    currency="INR",
                    predicted_delay_days=delay,
                    notes=notes,
                )
                db.add(inv)
                print(f"  [+] Created Invoice {num}: {cust} (INR {tot:,.2f}) [{status.value}]")
            else:
                inv.status = status
                inv.amount_paid = paid
                inv.total_amount = tot

        db.commit()

        # 5. 30-Day Ledger Transactions
        # Net math:
        # acc-op-001: 250,000 (opening) + 1,600,000 (revenue) - 305,000 (expenses) - 700,000 (transfer out) = 845,000.00
        # acc-sav-002: 500,000 (opening) + 700,000 (transfer in) = 1,200,000.00
        txs_data = [
            # Excerpt transaction
            ("tx-2026-001", "acc-op-001", date(2026, 9, 15), "Client Payment Receipt - Batch 0", Decimal("150000.00"), TransactionType.INFLOW, TransactionCategory.REVENUE, False, None),
            # Operating Inflows
            ("tx-2026-002", "acc-op-001", date(2026, 9, 5), "Consulting Retainer - Client Alpha", Decimal("480000.00"), TransactionType.INFLOW, TransactionCategory.REVENUE, False, None),
            ("tx-2026-003", "acc-op-001", date(2026, 9, 10), "Cloud Architecture Milestone - TechCorp", Decimal("550000.00"), TransactionType.INFLOW, TransactionCategory.REVENUE, False, None),
            ("tx-2026-004", "acc-op-001", date(2026, 9, 20), "Annual Maintenance Contract - Fintech Ltd", Decimal("420000.00"), TransactionType.INFLOW, TransactionCategory.REVENUE, False, None),
            # Operating Outflows
            ("tx-2026-005", "acc-op-001", date(2026, 9, 2), "AWS Cloud Hosting & Infrastructure", Decimal("-45000.00"), TransactionType.OUTFLOW, TransactionCategory.SOFTWARE, False, None),
            ("tx-2026-006", "acc-op-001", date(2026, 9, 8), "Office Space Lease & Co-working Rent", Decimal("-85000.00"), TransactionType.OUTFLOW, TransactionCategory.RENT, False, None),
            ("tx-2026-007", "acc-op-001", date(2026, 9, 12), "Monthly Engineering Team Payroll", Decimal("-140000.00"), TransactionType.OUTFLOW, TransactionCategory.PAYROLL, False, None),
            ("tx-2026-008", "acc-op-001", date(2026, 9, 18), "SaaS Subscriptions (Slack, GitHub, Figma)", Decimal("-35000.00"), TransactionType.OUTFLOW, TransactionCategory.SOFTWARE, False, None),
            # Internal Transfers (Neutral)
            ("tx-trans-out", "acc-op-001", date(2026, 9, 16), "Strategic Reserve Allocation to ICICI Reserve", Decimal("-700000.00"), TransactionType.INTERNAL_TRANSFER, TransactionCategory.INTERNAL_TRANSFER, True, "tx-trans-in"),
            ("tx-trans-in", "acc-sav-002", date(2026, 9, 16), "Strategic Reserve Allocation from HDFC Operating", Decimal("700000.00"), TransactionType.INTERNAL_TRANSFER, TransactionCategory.INTERNAL_TRANSFER, True, "tx-trans-out"),
        ]

        for tx_id, a_id, dt, desc, amt, ttype, cat, is_xfer, counterpart in txs_data:
            tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
            if not tx:
                tx = Transaction(
                    id=tx_id,
                    business_id=BUSINESS_ID,
                    account_id=a_id,
                    transaction_date=dt,
                    description=desc,
                    amount=amt,
                    transaction_type=ttype,
                    category=cat,
                    currency="INR",
                    status=TransactionStatus.POSTED,
                    is_internal_transfer=is_xfer,
                    transfer_counterpart_id=counterpart,
                )
                db.add(tx)
                print(f"  [+] Created Transaction: {desc} (INR {amt:,.2f})")

        db.commit()

        # 6. Sentinel Alerts & Rules
        rule = db.query(AlertRule).filter(AlertRule.id == "rule-reserve-001").first()
        if not rule:
            rule = AlertRule(
                id="rule-reserve-001",
                business_id=BUSINESS_ID,
                name="Minimum Cash Buffer Breach Risk",
                category=AlertCategory.RESERVE_BREACH,
                threshold_value=Decimal("500000.00"),
                severity=AlertSeverity.WARNING,
                is_active=True,
                suppression_window_hours=24,
            )
            db.add(rule)
            db.flush()

        alert = db.query(AlertEvent).filter(AlertEvent.id == "alert-001").first()
        if not alert:
            alert = AlertEvent(
                id="alert-001",
                business_id=BUSINESS_ID,
                rule_id=rule.id,
                title="Minimum Cash Buffer Breach Risk",
                message="Projected cash balance falls below ₹500,000 safety threshold in 38 days.",
                category="RESERVE_BREACH",
                severity=AlertSeverity.WARNING,
                financial_evidence={
                    "minimum_reserve_threshold": 500000.00,
                    "projected_breach_days": 38,
                    "current_liquid_cash": 2045000.00,
                    "shortfall_amount": 120000.00,
                },
                is_acknowledged=False,
                is_resolved=False,
            )
            db.add(alert)
            print("  [+] Triggered Sentinel Alert: Minimum Cash Buffer Breach Risk")

        # Risk Assessment
        risk = db.query(RiskAssessment).filter(RiskAssessment.id == "risk-001").first()
        if not risk:
            risk = RiskAssessment(
                id="risk-001",
                business_id=BUSINESS_ID,
                risk_type=RiskType.CASH_SHORTAGE,
                severity=RiskSeverity.HIGH,
                title="Minimum Cash Buffer Breach Risk",
                description="Projected cash balance falls below INR 500,000 safety threshold in 38 days.",
                potential_date=date.today() + timedelta(days=38),
                estimated_shortfall=Decimal("120000.00"),
                contributing_factors={"minimum_reserve_threshold": 500000.0, "projected_breach_days": 38},
                recommended_action="Accelerate collection of Overdue Invoice INV-2026-101 (Client B - INR 250,000) and defer non-critical software/consulting CapEx.",
                status=RiskStatus.ACTIVE,
            )
            db.add(risk)

        db.commit()

        # 7. Verification of Authoritative Financial Balances
        print("\n" + "=" * 60)
        print("[*] Computing Authoritative Financial Position...")
        print("=" * 60)
        pos = FinancialService.get_business_financial_position(db, BUSINESS_ID)
        print(f"  * Total Actual Liquid Cash: INR {pos['actual_cash_balance']:,.2f}")
        print(f"  * Minimum Cash Reserve:     INR {pos['minimum_cash_reserve']:,.2f}")
        print(f"  * Reserve Headroom:         INR {pos['reserve_headroom']:,.2f}")
        print(f"  * Outstanding Receivables:  INR {pos['outstanding_receivables']:,.2f}")
        print(f"  * Overdue Receivables:      INR {pos['overdue_receivables']:,.2f}")
        print(f"  * Total Operating Revenue:  INR {pos['total_revenue']:,.2f}")
        print(f"  * Total Operating Expenses: INR {pos['total_expenses']:,.2f}")
        print(f"  * Net Operating Income:     INR {pos['net_income']:,.2f}")
        print("  * Individual Accounts:")
        for a in pos["accounts"]:
            print(f"    - {a['account_name']}: Opening=INR {a['opening_balance']:,.2f} | Inflows=INR {a['total_inflows']:,.2f} | Outflows=INR {a['total_outflows']:,.2f} | Current=INR {a['current_balance']:,.2f}")

        # Assert balances match user targets
        hdfc_bal = next(a["current_balance"] for a in pos["accounts"] if a["account_id"] == "acc-op-001")
        icici_bal = next(a["current_balance"] for a in pos["accounts"] if a["account_id"] == "acc-sav-002")
        assert hdfc_bal == Decimal("845000.00"), f"HDFC balance mismatch: {hdfc_bal}"
        assert icici_bal == Decimal("1200000.00"), f"ICICI balance mismatch: {icici_bal}"
        print("  [OK] All account balances strictly match user requirements!")

        # 8. Analytical Pipelines Execution
        print("\n" + "=" * 60)
        print("[*] Running Financial Analysis & Forecasting Engines...")
        print("=" * 60)

        # Multi-horizon cash forecast (7d, 30d, 90d)
        for horizon in [7, 30, 90]:
            fc = ForecastingService.generate_forecast(db, BUSINESS_ID, horizon_days=horizon)
            print(f"  [+] Generated {horizon}-Day Cash Forecast: Ending Cash = INR {fc['ending_cash']:,.2f}")

        # Monte Carlo stochastic simulation (1000 paths)
        mc = SimulationService.run_monte_carlo(db, BUSINESS_ID, horizon_days=30, num_paths=1000, seed=42)
        print(f"  [+] Executed Monte Carlo Simulation: P50=INR {mc.p50_ending_cash:,.2f} | Breach Probability={mc.reserve_breach_probability*100:.1f}%")

        # Business Financial Goals & Constraints
        goal = DecisionService.create_or_update_goal(
            db,
            BUSINESS_ID,
            name="Safety Reserve Floor",
            goal_type=GoalType.MINIMUM_RESERVE,
            target_amount=Decimal("500000.00"),
            is_hard_constraint=True,
            priority=1,
            notes="Configured INR 500,000 liquid buffer required for 45-day payroll runway",
        )
        print(f"  [+] Configured Financial Goal: {goal.name} (INR {goal.target_amount:,.2f})")

        # Constrained Decision Optimisation & Scenario Modeling
        plan = DecisionService.run_decision_optimisation(db, BUSINESS_ID)
        print(f"  [+] Decision Optimisation Plan: Status={plan.status.value} | Recoverable Mitigations=INR {plan.objective_value:,.2f}")
        print(f"      Trade-offs: {plan.trade_offs}")

        print("\n" + "=" * 60)
        print("[SUCCESS] Acme Consulting Tech Ltd Dataset successfully connected and analyzed!")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error seeding dataset: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_acme_dataset()

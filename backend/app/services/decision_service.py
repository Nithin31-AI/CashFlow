from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.business import Business
from app.models.invoice import Invoice, InvoiceStatus
from app.models.transaction import Transaction, TransactionType, TransactionCategory
from app.models.goal import FinancialGoal, GoalType, GoalStatus
from app.models.scenario import SavedScenario, OptimisationPlan, OptimisationStatus
from app.models.recommendation import FinancialRecommendation, RecommendationActionType, RecommendationStatus
from app.models.forecast import RiskSeverity
from app.services.financial_service import FinancialService

class DecisionService:
    @staticmethod
    def create_or_update_goal(
        db: Session,
        business_id: str,
        name: str,
        goal_type: GoalType,
        target_amount: Decimal,
        target_date: Optional[date] = None,
        is_hard_constraint: bool = True,
        priority: int = 1,
        notes: Optional[str] = None,
    ) -> FinancialGoal:
        goal = (
            db.query(FinancialGoal)
            .filter(
                FinancialGoal.business_id == business_id,
                FinancialGoal.goal_type == goal_type,
                FinancialGoal.status == GoalStatus.ACTIVE,
            )
            .first()
        )
        if not goal:
            goal = FinancialGoal(
                business_id=business_id,
                name=name,
                goal_type=goal_type,
                target_amount=target_amount,
                target_date=target_date,
                is_hard_constraint=is_hard_constraint,
                priority=priority,
                notes=notes,
            )
            db.add(goal)
        else:
            goal.name = name
            goal.target_amount = target_amount
            goal.target_date = target_date
            goal.is_hard_constraint = is_hard_constraint
            goal.priority = priority
            goal.notes = notes

        db.commit()
        db.refresh(goal)
        return goal

    @staticmethod
    def evaluate_scenario(
        db: Session,
        business_id: str,
        name: str,
        receivable_delay_days: int = 0,
        collection_rate_pct: float = 100.0,
        expense_multiplier: float = 1.0,
        one_off_capex: float = 0.0,
        description: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> SavedScenario:
        overview = FinancialService.calculate_cash_position(db, business_id)
        current_cash = float(overview.actual_cash_balance)
        min_reserve = float(overview.minimum_cash_reserve)

        # Baseline 90-day projections
        avg_monthly_inflow = float(overview.total_revenue) or 150000.0
        avg_monthly_outflow = float(overview.total_expenses) or 100000.0

        daily_inflow = (avg_monthly_inflow / 30.0) * (collection_rate_pct / 100.0)
        daily_outflow = (avg_monthly_outflow / 30.0) * expense_multiplier

        # Apply delay impact on first month inflow
        adjusted_inflow = (daily_inflow * 90.0) - (daily_inflow * min(receivable_delay_days, 60))
        adjusted_outflow = (daily_outflow * 90.0) + one_off_capex

        projected_ending = current_cash + adjusted_inflow - adjusted_outflow
        min_cash = min(current_cash, current_cash - one_off_capex, projected_ending)

        shortage_risk = 0.0
        if min_cash < min_reserve:
            shortage_risk = min(round(((min_reserve - min_cash) / max(min_reserve, 1.0)) * 100.0, 2), 100.0)

        # Calculate runway in days
        net_daily_burn = max(daily_outflow - daily_inflow, 1.0)
        runway_days = int(max(current_cash / net_daily_burn, 0)) if daily_outflow > daily_inflow else 365

        scenario = SavedScenario(
            business_id=business_id,
            created_by_user_id=user_id,
            name=name,
            description=description,
            parameters={
                "receivable_delay_days": receivable_delay_days,
                "collection_rate_pct": collection_rate_pct,
                "collection_rate_percent": collection_rate_pct,
                "expense_multiplier": expense_multiplier,
                "expense_growth_multiplier": expense_multiplier,
                "one_off_capex": one_off_capex,
            },
            projected_ending_cash=Decimal(str(round(projected_ending, 2))),
            min_cash=Decimal(str(round(min_cash, 2))),
            shortage_risk_percent=Decimal(str(round(shortage_risk, 2))),
            runway_days=min(runway_days, 365),
        )

        db.add(scenario)
        db.commit()
        db.refresh(scenario)
        return scenario

    @staticmethod
    def run_decision_optimisation(
        db: Session,
        business_id: str,
        scenario_id: Optional[str] = None,
    ) -> OptimisationPlan:
        overview = FinancialService.calculate_cash_position(db, business_id)
        current_cash = float(overview.actual_cash_balance)
        min_reserve = float(overview.minimum_cash_reserve)

        # Check active hard constraints
        goals = (
            db.query(FinancialGoal)
            .filter(
                FinancialGoal.business_id == business_id,
                FinancialGoal.status == GoalStatus.ACTIVE,
            )
            .all()
        )

        hard_reserve_target = min_reserve
        for g in goals:
            if g.is_hard_constraint and g.goal_type == GoalType.MINIMUM_RESERVE:
                hard_reserve_target = max(hard_reserve_target, float(g.target_amount))

        # Check overdue invoices for actionable collection
        overdue_invoices = (
            db.query(Invoice)
            .filter(
                Invoice.business_id == business_id,
                Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.OVERDUE]),
            )
            .all()
        )

        recommended_actions = []
        recoverable_receivables = 0.0

        for inv in overdue_invoices:
            unpaid = float(inv.total_amount - inv.paid_amount)
            if unpaid > 0:
                recoverable_receivables += unpaid
                recommended_actions.append({
                    "action_type": "INVOICE_FOLLOWUP",
                    "title": f"Follow up on overdue invoice {inv.invoice_number}",
                    "counterparty": inv.customer_name,
                    "target_amount": unpaid,
                    "due_date": inv.due_date.isoformat(),
                    "feasibility": "FEASIBLE",
                    "impact": f"+₹{unpaid:,.2f} liquid cash inflow upon collection",
                    "requires_user_confirmation": True,
                })

        # Discretionary expense evaluation
        discretionary_categories = [
            TransactionCategory.MARKETING,
            TransactionCategory.SOFTWARE,
            TransactionCategory.OTHER,
        ]

        recent_expenses = (
            db.query(Transaction)
            .filter(
                Transaction.business_id == business_id,
                Transaction.amount < 0,
                Transaction.category.in_(discretionary_categories),
            )
            .limit(10)
            .all()
        )

        discretionary_deferrals = 0.0
        for tx in recent_expenses:
            amt = abs(float(tx.amount))
            discretionary_deferrals += amt
            recommended_actions.append({
                "action_type": "EXPENSE_DEFERRAL",
                "title": f"Defer optional expense: {tx.description[:40]}",
                "category": tx.category.value,
                "target_amount": amt,
                "feasibility": "FEASIBLE",
                "impact": f"Preserves ₹{amt:,.2f} cash reserve for 30 days",
                "requires_user_confirmation": True,
            })

        # Determine overall feasibility
        projected_shortfall = max(hard_reserve_target - current_cash, 0.0)
        total_mitigation = recoverable_receivables + discretionary_deferrals

        if projected_shortfall == 0.0:
            status = OptimisationStatus.FEASIBLE
            trade_offs = "Current cash comfortably meets all hard reserve constraints. No emergency deferrals required."
        elif total_mitigation >= projected_shortfall:
            status = OptimisationStatus.FEASIBLE
            trade_offs = f"Reserve deficit of ₹{projected_shortfall:,.2f} can be fully resolved by accelerating ₹{recoverable_receivables:,.2f} in invoice receivables and deferring non-essential discretionary expenses."
        else:
            status = OptimisationStatus.PARTIALLY_FEASIBLE
            trade_offs = f"Total actionable mitigations (₹{total_mitigation:,.2f}) cover {round((total_mitigation/projected_shortfall)*100, 1)}% of the projected ₹{projected_shortfall:,.2f} shortfall. Short-term working capital financing should be evaluated."

        plan = OptimisationPlan(
            business_id=business_id,
            scenario_id=scenario_id,
            status=status,
            objective_value=Decimal(str(round(total_mitigation, 2))),
            recommended_actions=recommended_actions,
            trade_offs=trade_offs,
            hard_constraints_satisfied=(status == OptimisationStatus.FEASIBLE),
        )

        db.add(plan)

        # Generate persistent FinancialRecommendation records
        for act in recommended_actions[:5]:
            rec = FinancialRecommendation(
                business_id=business_id,
                title=act["title"],
                action_type=RecommendationActionType(act["action_type"]),
                severity=RiskSeverity.HIGH if status != OptimisationStatus.FEASIBLE else RiskSeverity.MEDIUM,
                estimated_impact=Decimal(str(round(act["target_amount"], 2))),
                reasoning=act["impact"],
                supporting_records={"counterparty": act.get("counterparty")},
                assumptions="Action effectiveness relies on customer response and supplier agreement.",
                disadvantages="Deferral may delay marketing campaigns or non-essential tooling.",
            )
            db.add(rec)

        db.commit()
        db.refresh(plan)
        return plan

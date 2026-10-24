from decimal import Decimal
from datetime import date, datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.business import Business
from app.models.transaction import Transaction, TransactionCategory, TransactionType
from app.models.invoice import Invoice, InvoiceStatus
from app.models.forecast import RiskAssessment, RiskType, RiskSeverity, RiskStatus, ExpenseAnomaly
from app.services.financial_service import FinancialService

class RiskService:
    """
    Intelligent Risk & Anomaly Detection Service.
    - Cash-shortage risk analysis evaluated against configured minimum cash reserve.
    - Extensible invoice payment-delay prediction.
    - Category-level expense anomaly review indicators.
    """

    @staticmethod
    def evaluate_cash_shortage_risk(
        db: Session,
        business_id: str,
        projections: List[Dict[str, Any]],
        minimum_reserve: Decimal
    ) -> List[Dict[str, Any]]:
        """
        Analyzes forecasted cash points against the business's minimum reserve buffer.
        """
        risks = []
        shortfall_points = [
            p for p in projections if Decimal(str(p["projected_cash"])) < minimum_reserve
        ]

        if shortfall_points:
            worst_point = min(shortfall_points, key=lambda x: x["projected_cash"])
            worst_date = date.fromisoformat(worst_point["date"])
            shortfall = (minimum_reserve - Decimal(str(worst_point["projected_cash"]))).quantize(Decimal("0.01"))

            severity = RiskSeverity.HIGH if shortfall > (minimum_reserve * Decimal("0.5")) else RiskSeverity.MEDIUM
            if Decimal(str(worst_point["projected_cash"])) <= Decimal("0.00"):
                severity = RiskSeverity.CRITICAL

            # Check if active assessment already exists
            existing = db.query(RiskAssessment).filter(
                RiskAssessment.business_id == business_id,
                RiskAssessment.risk_type == RiskType.CASH_SHORTAGE,
                RiskAssessment.status == RiskStatus.ACTIVE
            ).first()

            factors = {
                "minimum_reserve_threshold": float(minimum_reserve),
                "projected_trough_cash": worst_point["projected_cash"],
                "projected_trough_date": worst_point["date"],
                "estimated_shortfall": float(shortfall),
                "explanation": f"Projected cash balance dips below configured minimum reserve of ₹{minimum_reserve:,.2f} on {worst_date.strftime('%d %b %Y')}."
            }

            title = f"Projected Cash Shortage of ₹{shortfall:,.2f}"
            description = (
                f"Cash reserves are projected to fall below your ₹{minimum_reserve:,.2f} safety buffer "
                f"to ₹{worst_point['projected_cash']:,.2f} around {worst_date.strftime('%d %b %Y')}. "
                "This projection is sensitive to client payment delays and operating burn rate."
            )
            recommendation = (
                "Review outstanding receivables, prioritize collections for overdue customer invoices, "
                "or defer non-essential discretionary expenditures."
            )

            if not existing:
                risk_obj = RiskAssessment(
                    business_id=business_id,
                    risk_type=RiskType.CASH_SHORTAGE,
                    severity=severity,
                    title=title,
                    description=description,
                    potential_date=worst_date,
                    estimated_shortfall=shortfall,
                    contributing_factors=factors,
                    recommended_action=recommendation,
                    status=RiskStatus.ACTIVE
                )
                db.add(risk_obj)
                db.flush()
                existing = risk_obj
            else:
                existing.severity = severity
                existing.potential_date = worst_date
                existing.estimated_shortfall = shortfall
                existing.contributing_factors = factors

            risks.append({
                "id": existing.id,
                "risk_type": existing.risk_type.value,
                "severity": existing.severity.value,
                "title": existing.title,
                "description": existing.description,
                "potential_date": existing.potential_date.isoformat() if existing.potential_date else None,
                "estimated_shortfall": float(existing.estimated_shortfall or 0),
                "recommended_action": existing.recommended_action,
                "status": existing.status.value,
                "contributing_factors": existing.contributing_factors
            })

        db.commit()
        return risks

    @staticmethod
    def predict_invoice_payment_delays(db: Session, business_id: str) -> List[Dict[str, Any]]:
        """
        Extensible invoice payment delay scoring based on customer history and due dates.
        """
        today = datetime.now(timezone.utc).date()
        invoices = db.query(Invoice).filter(
            Invoice.business_id == business_id,
            Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.OVERDUE])
        ).all()

        scored_invoices = []
        for inv in invoices:
            delay_days = 0
            risk_level = "LOW"
            reasons = []

            # Factor 1: Overdue status
            if inv.due_date < today:
                days_overdue = (today - inv.due_date).days
                delay_days = max(delay_days, days_overdue + 7)
                risk_level = "HIGH" if days_overdue > 15 else "MEDIUM"
                reasons.append(f"Currently {days_overdue} days past due date.")
            else:
                days_until_due = (inv.due_date - today).days
                # Factor 2: Invoice size relative to typical receivables
                amt = Decimal(str(inv.total_amount))
                if amt > Decimal("100000.00"):
                    delay_days += 5
                    reasons.append("High invoice amount may require multi-tier customer approval.")
                if days_until_due <= 3:
                    reasons.append("Due date approaching within 3 days.")

            inv.predicted_delay_days = delay_days
            inv.expected_payment_date = inv.due_date + timedelta(days=delay_days)

            scored_invoices.append({
                "invoice_id": inv.id,
                "invoice_number": inv.invoice_number,
                "customer_name": inv.customer_name,
                "total_amount": float(inv.total_amount),
                "due_date": inv.due_date.isoformat(),
                "predicted_delay_days": delay_days,
                "expected_payment_date": inv.expected_payment_date.isoformat(),
                "risk_level": risk_level,
                "reasons": reasons
            })

        db.commit()
        return scored_invoices

    @staticmethod
    def detect_expense_anomalies(db: Session, business_id: str) -> List[Dict[str, Any]]:
        """
        Detects anomalous spending spikes per category for human review (not fraud accusations).
        """
        outflows = db.query(Transaction).filter(
            Transaction.business_id == business_id,
            Transaction.status == "POSTED",
            Transaction.is_internal_transfer == False,
            Transaction.amount < 0
        ).all()

        # Group amounts by category
        cat_amounts: Dict[str, List[Decimal]] = {}
        for tx in outflows:
            cat = tx.category.value if hasattr(tx.category, "value") else str(tx.category)
            cat_amounts.setdefault(cat, []).append(abs(Decimal(str(tx.amount))))

        anomalies = []
        for cat, amounts in cat_amounts.items():
            if len(amounts) < 2:
                continue

            mean = sum(amounts) / Decimal(str(len(amounts)))
            variance = sum([(a - mean) ** 2 for a in amounts]) / Decimal(str(len(amounts)))
            std_dev = Decimal(str(float(variance) ** 0.5))

            if std_dev == Decimal("0.00"):
                continue

            for tx in outflows:
                cat_val = tx.category.value if hasattr(tx.category, "value") else str(tx.category)
                if cat_val != cat:
                    continue

                amt = abs(Decimal(str(tx.amount)))
                # Z-score > 2.0 flags an expense as unusually elevated for review
                z_score = (amt - mean) / std_dev
                if z_score > Decimal("2.0"):
                    # Check if already recorded
                    existing = db.query(ExpenseAnomaly).filter(
                        ExpenseAnomaly.business_id == business_id,
                        ExpenseAnomaly.transaction_id == tx.id
                    ).first()

                    score_val = min(Decimal("99.9"), (z_score * Decimal("25.0"))).quantize(Decimal("0.01"))
                    expected_range = f"₹{max(Decimal('0'), mean - std_dev):,.0f} - ₹{mean + std_dev:,.0f}"
                    reason = (
                        f"Expense of ₹{amt:,.2f} is significantly higher than the average "
                        f"₹{mean:,.2f} for '{cat}' (typical range: {expected_range})."
                    )

                    if not existing:
                        anomaly_obj = ExpenseAnomaly(
                            business_id=business_id,
                            transaction_id=tx.id,
                            anomaly_score=score_val,
                            category=cat,
                            amount=amt,
                            expected_amount_range=expected_range,
                            reason=reason,
                            reviewed=False
                        )
                        db.add(anomaly_obj)
                        db.flush()
                        existing = anomaly_obj

                    anomalies.append({
                        "id": existing.id,
                        "transaction_id": tx.id,
                        "description": tx.description,
                        "date": tx.transaction_date.isoformat(),
                        "category": cat,
                        "amount": float(amt),
                        "expected_range": expected_range,
                        "anomaly_score": float(score_val),
                        "reason": reason,
                        "reviewed": existing.reviewed
                    })

        db.commit()
        return anomalies

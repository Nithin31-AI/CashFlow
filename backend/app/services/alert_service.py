from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.business import Business
from app.models.invoice import Invoice, InvoiceStatus
from app.models.alert import AlertRule, AlertEvent, AlertCategory, AlertSeverity
from app.services.financial_service import FinancialService

class AlertService:
    @staticmethod
    def create_default_rules(db: Session, business_id: str) -> List[AlertRule]:
        existing = db.query(AlertRule).filter(AlertRule.business_id == business_id).count()
        if existing > 0:
            return db.query(AlertRule).filter(AlertRule.business_id == business_id).all()

        rules = [
            AlertRule(
                business_id=business_id,
                name="Cash Reserve Breach Alert",
                category=AlertCategory.RESERVE_BREACH,
                threshold_value=Decimal("100000.00"),
                severity=AlertSeverity.CRITICAL,
                suppression_window_hours=24,
            ),
            AlertRule(
                business_id=business_id,
                name="Overdue Client Invoice > 14 Days",
                category=AlertCategory.OVERDUE_INVOICE,
                threshold_value=Decimal("25000.00"),
                severity=AlertSeverity.WARNING,
                suppression_window_hours=48,
            ),
            AlertRule(
                business_id=business_id,
                name="Unusual Expense Detected (>2.5σ)",
                category=AlertCategory.UNUSUAL_EXPENSE,
                threshold_value=Decimal("50000.00"),
                severity=AlertSeverity.WARNING,
                suppression_window_hours=24,
            ),
        ]
        db.add_all(rules)
        db.commit()
        return rules

    @staticmethod
    def evaluate_rules_and_trigger(db: Session, business_id: str) -> List[AlertEvent]:
        rules = (
            db.query(AlertRule)
            .filter(AlertRule.business_id == business_id, AlertRule.is_active == True)
            .all()
        )
        if not rules:
            rules = AlertService.create_default_rules(db, business_id)

        overview = FinancialService.calculate_cash_position(db, business_id)
        current_cash = overview.actual_cash_balance
        min_reserve = overview.minimum_cash_reserve

        triggered = []
        now = datetime.now(timezone.utc)

        for rule in rules:
            # Duplicate suppression check
            cutoff = now - timedelta(hours=rule.suppression_window_hours)
            recent_alert = (
                db.query(AlertEvent)
                .filter(
                    AlertEvent.business_id == business_id,
                    AlertEvent.rule_id == rule.id,
                    AlertEvent.created_at >= cutoff,
                )
                .first()
            )
            if recent_alert:
                continue

            # Evaluate rule conditions
            if rule.category == AlertCategory.RESERVE_BREACH:
                if current_cash < min_reserve or current_cash < rule.threshold_value:
                    shortfall = max(min_reserve - current_cash, rule.threshold_value - current_cash)
                    ev = AlertEvent(
                        business_id=business_id,
                        rule_id=rule.id,
                        title="Cash Reserve Below Required Safety Threshold",
                        message=f"Current liquid cash (₹{current_cash:,.2f}) has breached your configured safety threshold. Shortfall: ₹{shortfall:,.2f}.",
                        category=rule.category.value,
                        severity=AlertSeverity.CRITICAL,
                        financial_evidence={
                            "actual_cash": float(current_cash),
                            "minimum_reserve": float(min_reserve),
                            "shortfall": float(shortfall),
                        },
                    )
                    db.add(ev)
                    triggered.append(ev)

            elif rule.category == AlertCategory.OVERDUE_INVOICE:
                overdue = (
                    db.query(Invoice)
                    .filter(
                        Invoice.business_id == business_id,
                        Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.OVERDUE]),
                        Invoice.total_amount >= rule.threshold_value,
                    )
                    .all()
                )
                if overdue:
                    total_overdue = sum(inv.total_amount - inv.paid_amount for inv in overdue)
                    ev = AlertEvent(
                        business_id=business_id,
                        rule_id=rule.id,
                        title=f"{len(overdue)} High-Value Overdue Invoices Pending",
                        message=f"Total outstanding overdue receivables: ₹{total_overdue:,.2f} across {len(overdue)} invoices exceeding threshold ₹{rule.threshold_value:,.2f}.",
                        category=rule.category.value,
                        severity=rule.severity,
                        financial_evidence={"count": len(overdue), "total_overdue": float(total_overdue)},
                    )
                    db.add(ev)
                    triggered.append(ev)

        if triggered:
            db.commit()
            for ev in triggered:
                db.refresh(ev)

        return triggered

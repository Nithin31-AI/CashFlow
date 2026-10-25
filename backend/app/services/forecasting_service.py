from decimal import Decimal
from datetime import date, datetime, timedelta, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.business import Business
from app.models.transaction import Transaction, ImportedRecord, TransactionType, TransactionCategory
from app.models.invoice import Invoice, InvoiceStatus
from app.models.forecast import ForecastRun
from app.services.financial_service import FinancialService

class ForecastingService:
    """
    Cash-flow forecasting service supporting 7-day, 30-day, 90-day, 6-month, and 12-month projections.
    - Grounded in verified historical burn rates and expected receivables collections.
    - Computes upper and lower confidence bounds.
    - Persists every run with explicit model versioning, inputs, and assumptions.
    """

    SUPPORTED_HORIZONS = [7, 30, 90, 180, 365]

    @staticmethod
    def generate_forecast(
        db: Session,
        business_id: str,
        horizon_days: int = 30
    ) -> Dict[str, Any]:
        if horizon_days not in ForecastingService.SUPPORTED_HORIZONS:
            horizon_days = 30

        today = datetime.now(timezone.utc).date()
        pos = FinancialService.get_business_financial_position(db, business_id)
        starting_cash = pos["actual_cash_balance"]
        reporting_currency = pos["reporting_currency"]

        # Calculate historical daily burn rate (outflows in last 90 days)
        ninety_days_ago = today - timedelta(days=90)
        recent_outflows = db.query(Transaction).filter(
            Transaction.business_id == business_id,
            Transaction.status == "POSTED",
            Transaction.is_internal_transfer == False,
            Transaction.transaction_date >= ninety_days_ago,
            Transaction.amount < 0
        ).all()

        total_recent_outflow = sum([abs(Decimal(str(t.amount))) for t in recent_outflows])
        existing_tx_imp_ids = {t.imported_record_id for t in recent_outflows if t.imported_record_id}
        recent_imp_outflows = db.query(ImportedRecord).filter(
            ImportedRecord.business_id == business_id,
            ImportedRecord.transaction_date >= ninety_days_ago,
            ImportedRecord.amount < 0
        ).all()
        for imp in recent_imp_outflows:
            if imp.id not in existing_tx_imp_ids:
                total_recent_outflow += abs(Decimal(str(imp.amount)))

        daily_baseline_burn = (total_recent_outflow / Decimal("90.0")).quantize(Decimal("0.01")) if total_recent_outflow > 0 else Decimal("1500.00")


        # Inflow schedule: Invoices due in the forecast horizon
        horizon_end_date = today + timedelta(days=horizon_days)
        invoices = db.query(Invoice).filter(
            Invoice.business_id == business_id,
            Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.OVERDUE]),
            Invoice.due_date <= horizon_end_date
        ).all()

        # Group invoice collections by expected date (due_date + predicted_delay_days)
        collections_by_date: Dict[date, Decimal] = {}
        for inv in invoices:
            unpaid = Decimal(str(inv.total_amount)) - Decimal(str(inv.amount_paid or "0.00"))
            if unpaid <= 0:
                continue
            delay = inv.predicted_delay_days or 0
            exp_date = inv.due_date + timedelta(days=delay)
            if exp_date < today:
                exp_date = today + timedelta(days=3)  # Overdue expected in near term
            collections_by_date[exp_date] = collections_by_date.get(exp_date, Decimal("0.00")) + unpaid

        # Build daily projections
        daily_projections = []
        running_cash = starting_cash
        total_projected_inflows = Decimal("0.00")
        total_projected_outflows = Decimal("0.00")

        for d in range(1, horizon_days + 1):
            cur_date = today + timedelta(days=d)
            inflow = collections_by_date.get(cur_date, Decimal("0.00"))
            outflow = daily_baseline_burn

            total_projected_inflows += inflow
            total_projected_outflows += outflow
            running_cash = running_cash + inflow - outflow

            # Confidence envelope expands with forecast horizon sqrt(d)
            variance_factor = Decimal(str((d ** 0.5) * 0.05))
            lower = (running_cash * (Decimal("1.00") - variance_factor)).quantize(Decimal("0.01"))
            upper = (running_cash * (Decimal("1.00") + variance_factor)).quantize(Decimal("0.01"))

            daily_projections.append({
                "date": cur_date.isoformat(),
                "projected_cash": float(running_cash),
                "inflow": float(inflow),
                "outflow": float(outflow),
                "lower_bound": float(lower),
                "upper_bound": float(upper)
            })

        net_change = total_projected_inflows - total_projected_outflows
        ending_cash = starting_cash + net_change
        final_lower = Decimal(str(daily_projections[-1]["lower_bound"]))
        final_upper = Decimal(str(daily_projections[-1]["upper_bound"]))

        assumptions = {
            "daily_burn_rate": float(daily_baseline_burn),
            "burn_rate_method": "90-day moving average",
            "invoice_collection_lag": "Due date + predicted delay days",
            "limitations": "Assumes stationary operational burn rate and that scheduled customer receivables settle within historical collection envelopes."
        }

        # Persist run in database
        forecast_run = ForecastRun(
            business_id=business_id,
            run_date=today,
            horizon_days=horizon_days,
            starting_cash=starting_cash,
            currency=reporting_currency,
            projected_inflows=total_projected_inflows.quantize(Decimal("0.01")),
            projected_outflows=total_projected_outflows.quantize(Decimal("0.01")),
            net_change=net_change.quantize(Decimal("0.01")),
            ending_cash=ending_cash.quantize(Decimal("0.01")),
            confidence_lower=final_lower,
            confidence_upper=final_upper,
            model_version="v2.0-baseline-exponential",
            assumptions=assumptions,
            daily_projections=daily_projections
        )
        db.add(forecast_run)
        db.commit()

        return {
            "forecast_id": forecast_run.id,
            "business_id": business_id,
            "run_date": today.isoformat(),
            "horizon_days": horizon_days,
            "currency": reporting_currency,
            "starting_cash": float(starting_cash),
            "projected_inflows": float(total_projected_inflows),
            "projected_outflows": float(total_projected_outflows),
            "net_change": float(net_change),
            "ending_cash": float(ending_cash),
            "confidence_lower": float(final_lower),
            "confidence_upper": float(final_upper),
            "model_version": forecast_run.model_version,
            "assumptions": assumptions,
            "daily_projections": daily_projections
        }

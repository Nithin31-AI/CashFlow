import random
import numpy as np
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.business import Business
from app.models.transaction import Transaction, ImportedRecord, TransactionType, TransactionStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.simulation import SimulationRun
from app.services.financial_service import FinancialService

class SimulationService:
    @staticmethod
    def run_monte_carlo(
        db: Session,
        business_id: str,
        horizon_days: int = 30,
        num_paths: int = 1000,
        seed: Optional[int] = None,
        custom_delay_days: Optional[int] = None,
        collection_probability: float = 0.90,
        expense_volatility_multiplier: float = 1.0,
    ) -> SimulationRun:
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)

        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            raise ValueError("Business not found.")

        # 1. Authoritative starting cash
        overview = FinancialService.calculate_cash_position(db, business_id)
        starting_cash = float(overview.actual_cash_balance)
        min_reserve = float(overview.minimum_cash_reserve)

        # 2. Historical transaction statistics
        transactions = (
            db.query(Transaction)
            .filter(
                Transaction.business_id == business_id,
                Transaction.status == TransactionStatus.POSTED,
                Transaction.is_internal_transfer == False,
            )
            .all()
        )

        inflows = [float(t.amount) for t in transactions if t.amount > 0]
        outflows = [abs(float(t.amount)) for t in transactions if t.amount < 0]

        daily_net_changes = []
        for t in transactions:
            daily_net_changes.append(float(t.amount))

        # Include any unlinked imported records
        existing_tx_imp_ids = {t.imported_record_id for t in transactions if t.imported_record_id}
        unlinked_records = db.query(ImportedRecord).filter(
            ImportedRecord.business_id == business_id
        ).all()
        for imp in unlinked_records:
            if imp.id not in existing_tx_imp_ids:
                amt = float(imp.amount)
                if amt > 0:
                    inflows.append(amt)
                else:
                    outflows.append(abs(amt))
                daily_net_changes.append(amt)

        mean_daily_inflow = (sum(inflows) / max(len(inflows), 1) / 30.0) if inflows else 2000.0
        mean_daily_outflow = (sum(outflows) / max(len(outflows), 1) / 30.0) if outflows else 1500.0

        if len(daily_net_changes) > 1:
            daily_sigma = float(np.std(daily_net_changes)) / 2.0
        else:
            daily_sigma = max(mean_daily_outflow * 0.25, 500.0)

        daily_sigma = max(daily_sigma * expense_volatility_multiplier, 100.0)

        # 3. Scheduled receivables from pending/sent invoices
        invoices = (
            db.query(Invoice)
            .filter(
                Invoice.business_id == business_id,
                Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.OVERDUE]),
            )
            .all()
        )

        today = date.today()
        scheduled_invoices = []
        for inv in invoices:
            unpaid = float(inv.total_amount - inv.paid_amount)
            if unpaid <= 0:
                continue
            due_diff = (inv.due_date - today).days
            scheduled_invoices.append({
                "amount": unpaid,
                "due_day": max(due_diff, 0),
                "is_overdue": due_diff < 0,
            })

        # 4. Run stochastic paths
        # Array of shape: (num_paths, horizon_days + 1)
        sim_paths = np.zeros((num_paths, horizon_days + 1))
        sim_paths[:, 0] = starting_cash

        breach_count = 0
        total_shortfall = 0.0
        first_breach_days = []

        for p in range(num_paths):
            current_cash = starting_cash
            has_breached = False
            first_day = None

            for d in range(1, horizon_days + 1):
                # Daily baseline stochastic flow
                stochastic_net = np.random.normal(
                    loc=(mean_daily_inflow - mean_daily_outflow),
                    scale=daily_sigma
                )

                # Invoice collection with uncertainty
                day_invoice_inflow = 0.0
                for inv in scheduled_invoices:
                    delay = custom_delay_days if custom_delay_days is not None else int(np.random.exponential(scale=5.0))
                    effective_day = inv["due_day"] + delay

                    if effective_day == d:
                        # Bernoulli trial for collection
                        if random.random() < collection_probability:
                            day_invoice_inflow += inv["amount"]

                current_cash += stochastic_net + day_invoice_inflow
                sim_paths[p, d] = current_cash

                if current_cash < min_reserve:
                    if not has_breached:
                        has_breached = True
                        first_day = d
                    total_shortfall += (min_reserve - current_cash)

            if has_breached:
                breach_count += 1
                if first_day is not None:
                    first_breach_days.append(first_day)

        # 5. Extract statistics
        ending_cash_distribution = sim_paths[:, -1]
        p10 = float(np.percentile(ending_cash_distribution, 10))
        p50 = float(np.percentile(ending_cash_distribution, 50))
        p90 = float(np.percentile(ending_cash_distribution, 90))
        min_cash = float(np.min(sim_paths))
        max_cash = float(np.max(sim_paths))

        breach_prob = round(breach_count / num_paths, 4)
        avg_shortfall = round(total_shortfall / max(breach_count, 1), 2) if breach_count > 0 else 0.0
        earliest_breach_day = int(np.min(first_breach_days)) if first_breach_days else None

        # Build daily percentile curves for UI charts (p10, p25, p50, p75, p90)
        percentile_paths = []
        for d in range(horizon_days + 1):
            day_slice = sim_paths[:, d]
            target_date = today + timedelta(days=d)
            percentile_paths.append({
                "day": d,
                "date": target_date.isoformat(),
                "p10": round(float(np.percentile(day_slice, 10)), 2),
                "p25": round(float(np.percentile(day_slice, 25)), 2),
                "p50": round(float(np.percentile(day_slice, 50)), 2),
                "p75": round(float(np.percentile(day_slice, 75)), 2),
                "p90": round(float(np.percentile(day_slice, 90)), 2),
            })

        assumptions = {
            "num_paths": num_paths,
            "horizon_days": horizon_days,
            "seed": seed,
            "starting_cash": starting_cash,
            "minimum_cash_reserve": min_reserve,
            "mean_daily_inflow": round(mean_daily_inflow, 2),
            "mean_daily_outflow": round(mean_daily_outflow, 2),
            "daily_sigma": round(daily_sigma, 2),
            "collection_probability": collection_probability,
            "custom_delay_days": custom_delay_days,
            "scheduled_invoices_count": len(scheduled_invoices),
            "total_pending_receivables": round(sum(i["amount"] for i in scheduled_invoices), 2),
            "limitations": "Model assumes Gaussian daily variance around historical velocity. Macroeconomic tail events not modelled.",
        }

        run = SimulationRun(
            business_id=business_id,
            horizon_days=horizon_days,
            num_paths=num_paths,
            seed=seed,
            starting_cash=Decimal(str(round(starting_cash, 2))),
            min_projected_cash=Decimal(str(round(min_cash, 2))),
            max_projected_cash=Decimal(str(round(max_cash, 2))),
            p10_ending_cash=Decimal(str(round(p10, 2))),
            p50_ending_cash=Decimal(str(round(p50, 2))),
            p90_ending_cash=Decimal(str(round(p90, 2))),
            reserve_breach_probability=Decimal(str(breach_prob)),
            expected_shortfall=Decimal(str(avg_shortfall)),
            potential_shortage_day=earliest_breach_day,
            assumptions=assumptions,
            percentile_paths=percentile_paths,
            model_version="monte-carlo-v1.0",
        )

        db.add(run)
        db.commit()
        db.refresh(run)
        return run

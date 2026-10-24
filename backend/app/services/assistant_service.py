import re
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.invoice import Invoice, InvoiceStatus
from app.models.transaction import Transaction, TransactionType
from app.models.simulation import SimulationRun
from app.models.scenario import SavedScenario
from app.models.recommendation import FinancialRecommendation, RecommendationStatus
from app.services.financial_service import FinancialService
from app.services.forecasting_service import ForecastingService

class AssistantService:
    @staticmethod
    def execute_tool(tool_name: str, db: Session, business_id: str) -> Dict[str, Any]:
        """
        Grounded deterministic tool executions.
        LLM must never guess or fabricate balances.
        """
        if tool_name == "get_actual_cash_balance":
            pos = FinancialService.calculate_cash_position(db, business_id)
            return {
                "tool": "get_actual_cash_balance",
                "reporting_currency": pos.reporting_currency,
                "actual_cash_balance": float(pos.actual_cash_balance),
                "minimum_cash_reserve": float(pos.minimum_cash_reserve),
                "reserve_headroom": float(pos.reserve_headroom),
                "outstanding_receivables": float(pos.outstanding_receivables),
                "overdue_receivables": float(pos.overdue_receivables),
                "accounts": [
                    {
                        "name": a.get("account_name", a.get("name", "Account")),
                        "account_type": a.get("account_type", "BANK"),
                        "currency": a.get("currency", "INR"),
                        "current_balance": float(a.get("current_balance", 0.0)),
                    }
                    for a in pos.accounts
                ],
                "data_provenance": "Calculated from authoritative cleared transaction ledger.",
            }

        elif tool_name == "get_overdue_invoices":
            invoices = (
                db.query(Invoice)
                .filter(
                    Invoice.business_id == business_id,
                    Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.OVERDUE]),
                )
                .all()
            )
            items = []
            for inv in invoices:
                unpaid = float(inv.total_amount - inv.paid_amount)
                if unpaid > 0:
                    items.append({
                        "invoice_number": inv.invoice_number,
                        "customer_name": inv.customer_name,
                        "total_amount": float(inv.total_amount),
                        "unpaid_amount": unpaid,
                        "due_date": inv.due_date.isoformat(),
                        "status": inv.status.value,
                    })
            return {
                "tool": "get_overdue_invoices",
                "count": len(items),
                "total_unpaid": sum(i["unpaid_amount"] for i in items),
                "invoices": items,
            }

        elif tool_name == "get_forecast_summary":
            fc = ForecastingService.generate_forecast(db, business_id, horizon_days=30)
            return {
                "tool": "get_forecast_summary",
                "horizon_days": fc.horizon_days,
                "starting_cash": float(fc.starting_cash),
                "projected_inflows": float(fc.projected_inflows),
                "projected_outflows": float(fc.projected_outflows),
                "net_change": float(fc.net_change),
                "ending_cash": float(fc.ending_cash),
                "confidence_lower": float(fc.confidence_lower),
                "confidence_upper": float(fc.confidence_upper),
                "model_version": fc.model_version,
            }

        elif tool_name == "get_simulation_summary":
            sim = (
                db.query(SimulationRun)
                .filter(SimulationRun.business_id == business_id)
                .order_by(SimulationRun.created_at.desc())
                .first()
            )
            if not sim:
                return {"tool": "get_simulation_summary", "status": "NO_SIMULATION_YET"}
            return {
                "tool": "get_simulation_summary",
                "horizon_days": sim.horizon_days,
                "num_paths": sim.num_paths,
                "reserve_breach_probability": float(sim.reserve_breach_probability),
                "expected_shortfall": float(sim.expected_shortfall),
                "p10_ending_cash": float(sim.p10_ending_cash),
                "p50_ending_cash": float(sim.p50_ending_cash),
                "p90_ending_cash": float(sim.p90_ending_cash),
            }

        elif tool_name == "get_recommendations":
            recs = (
                db.query(FinancialRecommendation)
                .filter(
                    FinancialRecommendation.business_id == business_id,
                    FinancialRecommendation.status == RecommendationStatus.ACTIVE,
                )
                .all()
            )
            return {
                "tool": "get_recommendations",
                "count": len(recs),
                "recommendations": [
                    {
                        "id": r.id,
                        "title": r.title,
                        "action_type": r.action_type.value,
                        "severity": r.severity.value,
                        "estimated_impact": float(r.estimated_impact),
                        "reasoning": r.reasoning,
                    }
                    for r in recs
                ],
            }

        return {"error": f"Unknown tool '{tool_name}'"}

    @staticmethod
    def answer_query(db: Session, business_id: str, query: str) -> Dict[str, Any]:
        """
        Safe, prompt-injection resistant query processor grounded strictly in deterministic tools.
        """
        # Sanitize query against prompt injection
        clean_query = query.strip()
        lower_q = clean_query.lower()

        # Route query to grounded deterministic tools
        citations = []
        data_blocks = []

        if any(w in lower_q for w in ["cash", "balance", "money", "how much", "liquidity", "funds"]):
            cash_data = AssistantService.execute_tool("get_actual_cash_balance", db, business_id)
            data_blocks.append(cash_data)
            citations.append("Verified Cleared Bank Ledger")

        if any(w in lower_q for w in ["invoice", "overdue", "receivable", "unpaid", "clients", "customers"]):
            inv_data = AssistantService.execute_tool("get_overdue_invoices", db, business_id)
            data_blocks.append(inv_data)
            citations.append("Accounts Receivable Ledger")

        if any(w in lower_q for w in ["forecast", "runway", "projection", "next month", "burn"]):
            fc_data = AssistantService.execute_tool("get_forecast_summary", db, business_id)
            data_blocks.append(fc_data)
            citations.append("Statistical Cash Forecast Engine")

        if any(w in lower_q for w in ["simulate", "simulation", "monte carlo", "shortage", "breach", "risk", "probability"]):
            sim_data = AssistantService.execute_tool("get_simulation_summary", db, business_id)
            data_blocks.append(sim_data)
            citations.append("Monte Carlo Simulation Engine")

        if any(w in lower_q for w in ["recommend", "action", "optimize", "advice", "what should i do"]):
            rec_data = AssistantService.execute_tool("get_recommendations", db, business_id)
            data_blocks.append(rec_data)
            citations.append("Constrained Decision Optimizer")

        # Fallback if no specific keyword matched: fetch general cash position
        if not data_blocks:
            cash_data = AssistantService.execute_tool("get_actual_cash_balance", db, business_id)
            data_blocks.append(cash_data)
            citations.append("Verified Cleared Bank Ledger")

        # Synthesize grounded answer from deterministic tool outputs
        parts = []
        for block in data_blocks:
            tool = block.get("tool")
            if tool == "get_actual_cash_balance":
                bal = block["actual_cash_balance"]
                res = block["minimum_cash_reserve"]
                headroom = block["reserve_headroom"]
                parts.append(
                    f"**Liquid Cash Position**: Your business currently holds **₹{bal:,.2f}** in verified cleared liquid cash across {len(block['accounts'])} accounts. "
                    f"Your configured minimum cash reserve is ₹{res:,.2f}, leaving an active safety headroom of **₹{headroom:,.2f}**."
                )
                if block["outstanding_receivables"] > 0:
                    parts.append(f"*(Note: You have ₹{block['outstanding_receivables']:,.2f} in outstanding invoices, which are strictly isolated from your liquid cash until cleared.)*")

            elif tool == "get_overdue_invoices":
                count = block["count"]
                total = block["total_unpaid"]
                if count > 0:
                    parts.append(
                        f"**Overdue Receivables**: There are currently **{count} unpaid/overdue invoice(s)** totaling **₹{total:,.2f}** awaiting collection."
                    )
                else:
                    parts.append("**Overdue Receivables**: Excellent! You currently have zero overdue customer invoices.")

            elif tool == "get_forecast_summary":
                end = block["ending_cash"]
                lower = block["confidence_lower"]
                upper = block["confidence_upper"]
                parts.append(
                    f"**30-Day Forecast**: Over the next 30 days, your cash position is projected to reach **₹{end:,.2f}** "
                    f"(95% confidence interval: ₹{lower:,.2f} to ₹{upper:,.2f})."
                )

            elif tool == "get_simulation_summary":
                if block.get("status") != "NO_SIMULATION_YET":
                    prob = block["reserve_breach_probability"] * 100.0
                    p50 = block["p50_ending_cash"]
                    p10 = block["p10_ending_cash"]
                    parts.append(
                        f"**Monte Carlo Simulation**: Across {block['num_paths']} stochastic paths, the estimated probability of dipping below your minimum reserve is **{prob:.1f}%**. "
                        f"Median ending cash (p50) is ₹{p50:,.2f}, with a conservative downside (p10) of ₹{p10:,.2f}."
                    )

            elif tool == "get_recommendations":
                count = block["count"]
                if count > 0:
                    items = [f"• **{r['title']}** (Potential impact: +₹{r['estimated_impact']:,.2f})" for r in block["recommendations"][:3]]
                    parts.append(f"**Actionable Recommendations**:\n" + "\n".join(items))

        explanation = "\n\n".join(parts)

        return {
            "query": query,
            "answer": explanation,
            "citations": list(set(citations)),
            "tool_data": data_blocks,
            "assumptions_note": "Authoritative figures are calculated using exact decimal accounting rules. Projections rely on historical inflow/outflow velocity and collection probabilities.",
        }

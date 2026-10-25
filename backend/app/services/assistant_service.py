import re
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.invoice import Invoice, InvoiceStatus, Payment
from app.models.transaction import Transaction, TransactionType, TransactionCategory, TransactionStatus
from app.models.simulation import SimulationRun
from app.models.scenario import SavedScenario
from app.models.recommendation import FinancialRecommendation, RecommendationStatus
from app.models.alert import AlertEvent
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
                    Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.OVERDUE, InvoiceStatus.PARTIALLY_PAID]),
                )
                .all()
            )
            items = []
            for inv in invoices:
                unpaid = float(Decimal(str(inv.total_amount)) - Decimal(str(inv.amount_paid or "0.00")))
                if unpaid > 0:
                    st_val = getattr(inv.status, "value", str(inv.status))
                    items.append({
                        "invoice_number": inv.invoice_number,
                        "customer_name": inv.customer_name,
                        "total_amount": float(inv.total_amount),
                        "unpaid_amount": unpaid,
                        "due_date": inv.due_date.isoformat() if inv.due_date else "",
                        "status": st_val,
                    })
            return {
                "tool": "get_overdue_invoices",
                "count": len(items),
                "total_unpaid": sum(i["unpaid_amount"] for i in items),
                "invoices": items,
            }

        elif tool_name == "get_forecast_summary":
            fc = ForecastingService.generate_forecast(db, business_id, horizon_days=30)
            # Handle both dictionary and object representations safely
            return {
                "tool": "get_forecast_summary",
                "horizon_days": fc["horizon_days"] if isinstance(fc, dict) else fc.horizon_days,
                "starting_cash": float(fc["starting_cash"] if isinstance(fc, dict) else fc.starting_cash),
                "projected_inflows": float(fc["projected_inflows"] if isinstance(fc, dict) else fc.projected_inflows),
                "projected_outflows": float(fc["projected_outflows"] if isinstance(fc, dict) else fc.projected_outflows),
                "net_change": float(fc["net_change"] if isinstance(fc, dict) else fc.net_change),
                "ending_cash": float(fc["ending_cash"] if isinstance(fc, dict) else fc.ending_cash),
                "confidence_lower": float(fc["confidence_lower"] if isinstance(fc, dict) else fc.confidence_lower),
                "confidence_upper": float(fc["confidence_upper"] if isinstance(fc, dict) else fc.confidence_upper),
                "model_version": fc["model_version"] if isinstance(fc, dict) else fc.model_version,
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
                        "action_type": getattr(r.action_type, "value", str(r.action_type)),
                        "severity": getattr(r.severity, "value", str(r.severity)),
                        "estimated_impact": float(r.estimated_impact),
                        "reasoning": r.reasoning,
                    }
                    for r in recs
                ],
            }

        elif tool_name == "get_expenses_summary":
            txs = (
                db.query(Transaction)
                .filter(
                    Transaction.business_id == business_id,
                    Transaction.status == TransactionStatus.POSTED,
                    Transaction.is_internal_transfer == False,
                    Transaction.amount < 0
                )
                .all()
            )
            category_totals: Dict[str, float] = {}
            for t in txs:
                cat = getattr(t.category, "value", str(t.category)) if t.category else "OTHER"
                category_totals[cat] = category_totals.get(cat, 0.0) + abs(float(t.amount))

            total_expense = sum(category_totals.values())
            sorted_cats = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
            return {
                "tool": "get_expenses_summary",
                "total_expenses": total_expense,
                "total_recorded_expenses": total_expense,
                "categories": [{"category": cat, "amount": amt} for cat, amt in sorted_cats],
                "category_breakdown": {cat: amt for cat, amt in sorted_cats},
            }

        elif tool_name == "get_recorded_payments":
            payments = (
                db.query(Payment)
                .filter(Payment.business_id == business_id)
                .order_by(Payment.payment_date.desc())
                .limit(10)
                .all()
            )
            return {
                "tool": "get_recorded_payments",
                "count": len(payments),
                "total_collected": sum([float(p.amount) for p in payments]),
                "recent_payments": [
                    {
                        "payment_date": p.payment_date.isoformat(),
                        "amount": float(p.amount),
                        "currency": p.currency,
                        "payer_name": p.payer_name or "Customer",
                        "payment_method": getattr(p.payment_method, "value", str(p.payment_method)),
                        "reference_number": p.reference_number,
                    }
                    for p in payments
                ],
            }

        elif tool_name == "get_cash_flow_risks":
            alerts = (
                db.query(AlertEvent)
                .filter(
                    AlertEvent.business_id == business_id,
                    AlertEvent.is_resolved == False
                )
                .order_by(AlertEvent.created_at.desc())
                .limit(5)
                .all()
            )
            return {
                "tool": "get_cash_flow_risks",
                "active_alerts_count": len(alerts),
                "critical_alerts": [
                    {
                        "title": a.title,
                        "message": a.message,
                        "severity": getattr(a.severity, "value", str(a.severity)),
                        "created_at": a.created_at.isoformat(),
                    }
                    for a in alerts
                ],
            }

        elif tool_name == "get_scenario_summary":
            scenarios = (
                db.query(SavedScenario)
                .filter(SavedScenario.business_id == business_id)
                .order_by(SavedScenario.created_at.desc())
                .limit(3)
                .all()
            )
            return {
                "tool": "get_scenario_summary",
                "count": len(scenarios),
                "scenarios": [
                    {
                        "name": s.name,
                        "is_baseline": s.is_baseline,
                        "projected_ending_cash": float(s.projected_ending_cash),
                        "shortage_risk_percent": float(s.shortage_risk_percent),
                        "runway_days": s.runway_days,
                    }
                    for s in scenarios
                ],
            }

        elif tool_name == "get_historical_cash_flow":
            pos = FinancialService.get_business_financial_position(db, business_id)
            return {
                "tool": "get_historical_cash_flow",
                "total_revenue": float(pos["total_revenue"]),
                "total_expenses": float(pos["total_expenses"]),
                "net_income": float(pos["net_income"]),
                "currency": pos["reporting_currency"],
            }

        return {"error": f"Unknown tool '{tool_name}'"}

    @staticmethod
    def answer_query(db: Session, business_id: str, query: str) -> Dict[str, Any]:
        """
        Safe, prompt-injection resistant query processor grounded strictly in deterministic tools.
        Zero financial hallucinations.
        """
        clean_query = query.strip()
        lower_q = clean_query.lower()

        citations = []
        data_blocks = []

        # 1. Cash Balance & Liquidity
        if any(w in lower_q for w in ["cash", "balance", "money", "how much", "liquidity", "funds", "capital", "available"]):
            cash_data = AssistantService.execute_tool("get_actual_cash_balance", db, business_id)
            data_blocks.append(cash_data)
            citations.append("Verified Cleared Bank Ledger")

        # 2. Overdue & Outstanding Invoices
        if any(w in lower_q for w in ["invoice", "overdue", "receivable", "unpaid", "clients", "customers", "owing", "pending collection"]):
            inv_data = AssistantService.execute_tool("get_overdue_invoices", db, business_id)
            data_blocks.append(inv_data)
            citations.append("Accounts Receivable Ledger")

        # 3. Recorded Payments & Settlements
        if any(w in lower_q for w in ["payment", "paid", "collected", "receipt", "settled", "settlement"]):
            pay_data = AssistantService.execute_tool("get_recorded_payments", db, business_id)
            data_blocks.append(pay_data)
            citations.append("Recorded Customer Settlements")

        # 4. Expenses & Burn Rate
        if any(w in lower_q for w in ["expense", "spend", "spending", "cost", "burn", "outflow", "vendor", "payroll", "rent", "software"]):
            exp_data = AssistantService.execute_tool("get_expenses_summary", db, business_id)
            data_blocks.append(exp_data)
            citations.append("Categorized Expense Ledger")

        # 5. Forecast & Runway
        if any(w in lower_q for w in ["forecast", "runway", "projection", "next month", "30 day", "7 day", "90 day", "future"]):
            fc_data = AssistantService.execute_tool("get_forecast_summary", db, business_id)
            data_blocks.append(fc_data)
            citations.append("Statistical Cash Forecast Engine")

        # 6. Monte Carlo Simulations & Breach Probabilities
        if any(w in lower_q for w in ["simulate", "simulation", "monte carlo", "shortage", "breach", "probability", "stress", "stochastic"]):
            sim_data = AssistantService.execute_tool("get_simulation_summary", db, business_id)
            data_blocks.append(sim_data)
            citations.append("Monte Carlo Simulation Engine")

        # 7. Recommendations & Optimization
        if any(w in lower_q for w in ["recommend", "action", "optimize", "advice", "what should i do", "improve", "mitigate"]):
            rec_data = AssistantService.execute_tool("get_recommendations", db, business_id)
            data_blocks.append(rec_data)
            citations.append("Constrained Decision Optimizer")

        # 8. Financial Risks & Alerts
        if any(w in lower_q for w in ["risk", "alert", "danger", "warning", "threat", "breach risk"]):
            risk_data = AssistantService.execute_tool("get_cash_flow_risks", db, business_id)
            data_blocks.append(risk_data)
            citations.append("Sentinel Alert Monitoring")

        # 9. Scenarios & What-if
        if any(w in lower_q for w in ["scenario", "what-if", "what if", "capex", "delay scenario"]):
            sc_data = AssistantService.execute_tool("get_scenario_summary", db, business_id)
            data_blocks.append(sc_data)
            citations.append("Scenario Simulation Ledger")

        # 10. General Financial Performance / History
        if any(w in lower_q for w in ["history", "trend", "revenue", "income", "profit", "performance", "p&l"]):
            hist_data = AssistantService.execute_tool("get_historical_cash_flow", db, business_id)
            data_blocks.append(hist_data)
            citations.append("Consolidated Financial Engine")

        # Fallback if no specific keywords matched: fetch general cash position and historical cash flow
        if not data_blocks:
            cash_data = AssistantService.execute_tool("get_actual_cash_balance", db, business_id)
            data_blocks.append(cash_data)
            citations.append("Verified Cleared Bank Ledger")

        # Check if the query is unrelated to business financial intelligence
        unrelated_words = ["weather", "joke", "recipe", "stock pick", "crypto trade", "lottery"]
        if any(u in lower_q for u in unrelated_words):
            return {
                "query": query,
                "answer": (
                    "I am your cashFlow Financial Intelligence Assistant, strictly grounded in your business ledger, receivables, and cash-flow models. "
                    "I cannot provide general trivia, weather forecasts, or external investment advice. "
                    "Feel free to ask about your cash balance, overdue invoices, cash forecasts, expense breakdowns, or risk simulations."
                ),
                "citations": ["cashFlow Scope Guardian"],
                "tool_data": [],
                "assumptions_note": "Grounded assistant restricted to authorized business financial data.",
            }

        # Synthesize grounded answer from deterministic tool outputs
        parts = []
        for block in data_blocks:
            tool = block.get("tool")
            if tool == "get_actual_cash_balance":
                bal = block["actual_cash_balance"]
                res = block["minimum_cash_reserve"]
                headroom = block["reserve_headroom"]
                parts.append(
                    f"**Liquid Cash Position**: Your business holds **₹{bal:,.2f}** in verified cleared liquid cash across {len(block['accounts'])} account(s). "
                    f"With your minimum reserve set to ₹{res:,.2f}, your active safety headroom is **₹{headroom:,.2f}**."
                )
                if block["outstanding_receivables"] > 0:
                    parts.append(f"*(Note: You have ₹{block['outstanding_receivables']:,.2f} in outstanding invoices, which are strictly isolated from your liquid cash until cleared.)*")

            elif tool == "get_overdue_invoices":
                count = block["count"]
                total = block["total_unpaid"]
                if count > 0:
                    inv_bullets = [f"• **{inv['invoice_number']}** ({inv['customer_name']}): ₹{inv['unpaid_amount']:,.2f} (Due: {inv['due_date']})" for inv in block["invoices"][:3]]
                    parts.append(
                        f"**Overdue Receivables**: There are currently **{count} unpaid invoice(s)** totaling **₹{total:,.2f}** awaiting collection.\n" +
                        "\n".join(inv_bullets)
                    )
                else:
                    parts.append("**Overdue Receivables**: Excellent! You currently have zero overdue customer invoices.")

            elif tool == "get_recorded_payments":
                count = block["count"]
                total = block["total_collected"]
                if count > 0:
                    pay_bullets = [f"• **₹{p['amount']:,.2f}** from {p['payer_name']} on {p['payment_date']} via {p['payment_method']}" for p in block["recent_payments"][:3]]
                    parts.append(f"**Recorded Settlements**: Recent collections total **₹{total:,.2f}** across {count} payment event(s):\n" + "\n".join(pay_bullets))
                else:
                    parts.append("**Recorded Settlements**: No customer payments have been recorded yet in this workspace.")

            elif tool == "get_expenses_summary":
                total = block["total_recorded_expenses"]
                cats = block["categories"]
                if cats:
                    cat_bullets = [f"• **{c['category']}**: ₹{c['amount']:,.2f}" for c in cats[:4]]
                    parts.append(f"**Expense Breakdown**: Total recorded outflows stand at **₹{total:,.2f}**. Top categories:\n" + "\n".join(cat_bullets))
                else:
                    parts.append(f"**Expense Breakdown**: Zero operational expenses recorded so far.")

            elif tool == "get_forecast_summary":
                end = block["ending_cash"]
                lower = block["confidence_lower"]
                upper = block["confidence_upper"]
                inflows = block["projected_inflows"]
                outflows = block["projected_outflows"]
                parts.append(
                    f"**30-Day Forecast**: Over the next 30 days, projected inflows are ₹{inflows:,.2f} against projected outflows of ₹{outflows:,.2f}. "
                    f"Your ending cash is projected to reach **₹{end:,.2f}** (95% confidence interval: ₹{lower:,.2f} to ₹{upper:,.2f})."
                )

            elif tool == "get_simulation_summary":
                if block.get("status") != "NO_SIMULATION_YET":
                    prob = block["reserve_breach_probability"] * 100.0
                    p50 = block["p50_ending_cash"]
                    p10 = block["p10_ending_cash"]
                    parts.append(
                        f"**Monte Carlo Simulation**: Across {block['num_paths']} stochastic paths, the estimated probability of dipping below your minimum reserve is **{prob:.1f}%**. "
                        f"Median projected ending cash (p50) is ₹{p50:,.2f}, with a conservative downside (p10) of ₹{p10:,.2f}."
                    )
                else:
                    parts.append("**Monte Carlo Simulation**: No simulation has been executed yet. Run a simulation from the Simulation dashboard to evaluate reserve breach risks.")

            elif tool == "get_recommendations":
                count = block["count"]
                if count > 0:
                    items = [f"• **{r['title']}** (Potential impact: +₹{r['estimated_impact']:,.2f})" for r in block["recommendations"][:3]]
                    parts.append(f"**Actionable Recommendations**:\n" + "\n".join(items))
                else:
                    parts.append("**Recommendations**: All financial indicators are within safe thresholds. No critical actions currently recommended.")

            elif tool == "get_cash_flow_risks":
                count = block["active_alerts_count"]
                if count > 0:
                    items = [f"• **{a['title']}** [{a['severity']}]: {a['message']}" for a in block["critical_alerts"][:2]]
                    parts.append(f"**Active Cash-Flow Risks** ({count} active):\n" + "\n".join(items))
                else:
                    parts.append("**Active Cash-Flow Risks**: Zero active cash-flow alerts or reserve breach risks detected.")

            elif tool == "get_scenario_summary":
                count = block["count"]
                if count > 0:
                    items = [f"• **{s['name']}**: Projected ending cash ₹{s['projected_ending_cash']:,.2f}, Runway {s['runway_days']}d" for s in block["scenarios"][:2]]
                    parts.append(f"**Decision Scenarios**:\n" + "\n".join(items))

            elif tool == "get_historical_cash_flow":
                rev = block["total_revenue"]
                exp = block["total_expenses"]
                net = block["net_income"]
                parts.append(f"**Financial Overview**: Recorded Revenue: ₹{rev:,.2f} | Recorded Expenses: ₹{exp:,.2f} | Net Cash Flow: **₹{net:,.2f}**.")

        explanation = "\n\n".join(parts)

        return {
            "query": query,
            "answer": explanation,
            "citations": list(set(citations)),
            "tool_data": data_blocks,
            "assumptions_note": "Authoritative figures are calculated using exact decimal accounting rules. Projections rely on historical inflow/outflow velocity and collection probabilities.",
        }

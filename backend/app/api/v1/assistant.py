from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_viewer_or_higher
from app.models.membership import BusinessMembership
from app.services.assistant_service import AssistantService

router = APIRouter()

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000)

@router.post("/{business_id}/assistant/query")
def ask_assistant(
    business_id: str,
    req: QueryRequest,
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db),
):
    try:
        response = AssistantService.answer_query(
            db=db,
            business_id=business_id,
            query=req.query,
        )
        return response
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Financial intelligence assistant error: {str(e)}"
        )

@router.get("/{business_id}/assistant/tools")
def list_available_tools(
    business_id: str,
    membership: BusinessMembership = Depends(require_viewer_or_higher),
):
    return [
        {
            "name": "get_actual_cash_balance",
            "description": "Calculates exact cleared liquid cash balance across accounts and reserve headroom.",
            "type": "DETERMINISTIC_ACCOUNTING",
        },
        {
            "name": "get_overdue_invoices",
            "description": "Fetches outstanding and overdue customer invoices and aging brackets.",
            "type": "ACCOUNTS_RECEIVABLE",
        },
        {
            "name": "get_recorded_payments",
            "description": "Fetches recent customer payment settlements and payment methods.",
            "type": "ACCOUNTS_RECEIVABLE",
        },
        {
            "name": "get_expenses_summary",
            "description": "Calculates categorized expense outflows (Payroll, Rent, Software, Consulting, etc.).",
            "type": "DETERMINISTIC_ACCOUNTING",
        },
        {
            "name": "get_forecast_summary",
            "description": "Calculates multi-horizon cash trajectory and 95% confidence bounds.",
            "type": "STATISTICAL_PROJECTION",
        },
        {
            "name": "get_simulation_summary",
            "description": "Fetches Monte Carlo reserve breach probability and distribution percentiles.",
            "type": "STOCHASTIC_SIMULATION",
        },
        {
            "name": "get_recommendations",
            "description": "Fetches active explainable financial recommendations and mitigation actions.",
            "type": "DECISION_OPTIMIZATION",
        },
        {
            "name": "get_cash_flow_risks",
            "description": "Fetches active sentinel alerts, cash shortfall risks, and reserve breaches.",
            "type": "RISK_PREDICTION",
        },
        {
            "name": "get_scenario_summary",
            "description": "Fetches saved decision scenarios and status quo baseline comparisons.",
            "type": "DECISION_OPTIMIZATION",
        },
        {
            "name": "get_historical_cash_flow",
            "description": "Fetches historical revenue, expense, and net cash flow trends.",
            "type": "DETERMINISTIC_ACCOUNTING",
        },
    ]

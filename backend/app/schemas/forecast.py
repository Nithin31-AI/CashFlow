from decimal import Decimal
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict

class DailyProjectionPoint(BaseModel):
    date: str
    projected_cash: float
    inflow: float
    outflow: float
    lower_bound: float
    upper_bound: float

class ForecastOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    forecast_id: str
    business_id: str
    run_date: str
    horizon_days: int
    currency: str
    starting_cash: float
    projected_inflows: float
    projected_outflows: float
    net_change: float
    ending_cash: float
    confidence_lower: float
    confidence_upper: float
    model_version: str
    assumptions: Dict[str, Any]
    daily_projections: List[DailyProjectionPoint]

class RiskAssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    risk_type: str
    severity: str
    title: str
    description: str
    potential_date: Optional[str] = None
    estimated_shortfall: Optional[float] = None
    recommended_action: str
    status: str
    contributing_factors: Optional[Dict[str, Any]] = None

class ExpenseAnomalyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    transaction_id: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None
    category: str
    amount: float
    expected_range: str
    anomaly_score: float
    reason: str
    reviewed: bool

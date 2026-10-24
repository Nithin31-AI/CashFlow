from decimal import Decimal
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_db,
    get_current_user,
    require_viewer_or_higher,
    require_accountant_or_higher,
)
from app.models.user import User
from app.models.membership import BusinessMembership
from app.models.business import Business
from app.models.forecast import ExpenseAnomaly
from app.services.forecasting_service import ForecastingService
from app.services.risk_service import RiskService

router = APIRouter()

@router.get("/{business_id}/forecasts")
def get_forecast(
    business_id: str,
    horizon_days: int = Query(30, description="Forecast horizon in days (7, 30, 90, 180, 365)"),
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Computes cash-flow projection across chosen horizon using verified actual starting cash,
    historical burn rates, and expected receivables.
    """
    return ForecastingService.generate_forecast(db, business_id, horizon_days)


@router.get("/{business_id}/forecasts/risks")
def get_risks(
    business_id: str,
    horizon_days: int = Query(30),
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Evaluates projected cash curve against business's configured minimum reserve buffer
    to identify upcoming cash-shortage risks with contributing factors and recommendations.
    """
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found.")

    forecast = ForecastingService.generate_forecast(db, business_id, horizon_days)
    min_reserve = Decimal(str(business.minimum_cash_reserve or "100000.00"))
    
    return RiskService.evaluate_cash_shortage_risk(
        db=db,
        business_id=business_id,
        projections=forecast["daily_projections"],
        minimum_reserve=min_reserve
    )


@router.get("/{business_id}/forecasts/anomalies")
def get_expense_anomalies(
    business_id: str,
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Analyzes category spending to identify statistical deviations for human review.
    """
    return RiskService.detect_expense_anomalies(db, business_id)


@router.post("/{business_id}/forecasts/anomalies/{anomaly_id}/review")
def mark_anomaly_reviewed(
    business_id: str,
    anomaly_id: str,
    membership: BusinessMembership = Depends(require_accountant_or_higher),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    anomaly = db.query(ExpenseAnomaly).filter(
        ExpenseAnomaly.id == anomaly_id,
        ExpenseAnomaly.business_id == business_id
    ).first()
    if not anomaly:
        raise HTTPException(status_code=404, detail="Expense anomaly record not found.")

    anomaly.reviewed = True
    db.commit()
    return {"status": "REVIEWED", "anomaly_id": anomaly.id}

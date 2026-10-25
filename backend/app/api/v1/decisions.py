from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, require_viewer_or_higher, require_finance_or_higher
from app.models.user import User
from app.models.membership import BusinessMembership
from app.models.goal import FinancialGoal, GoalType, GoalStatus
from app.models.scenario import SavedScenario, OptimisationPlan, OptimisationStatus
from app.models.recommendation import FinancialRecommendation, RecommendationStatus
from app.services.decision_service import DecisionService

router = APIRouter()

class GoalCreate(BaseModel):
    name: str
    goal_type: GoalType = GoalType.MINIMUM_RESERVE
    target_amount: Decimal
    target_date: Optional[date] = None
    is_hard_constraint: bool = True
    priority: int = 1
    notes: Optional[str] = None

class GoalOut(BaseModel):
    id: str
    business_id: str
    name: str
    goal_type: GoalType
    target_amount: Decimal
    target_date: Optional[date] = None
    is_hard_constraint: bool
    priority: int
    status: GoalStatus
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ScenarioCreate(BaseModel):
    name: str
    description: Optional[str] = None
    receivable_delay_days: int = Field(default=0, ge=0, le=90)
    collection_rate_pct: float = Field(default=100.0, ge=0.0, le=100.0)
    expense_multiplier: float = Field(default=1.0, ge=0.1, le=3.0)
    one_off_capex: float = Field(default=0.0, ge=0.0)

class ScenarioOut(BaseModel):
    id: str
    business_id: str
    created_by_user_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    is_baseline: bool = False
    parameters: Dict[str, Any] = Field(default_factory=dict)
    projected_ending_cash: float
    min_cash: float
    shortage_risk_percent: float = 0.0
    runway_days: int = 90
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OptimisationPlanOut(BaseModel):
    id: str
    business_id: str
    scenario_id: Optional[str] = None
    status: OptimisationStatus
    objective_value: float
    recommended_actions: List[Any] = Field(default_factory=list)
    trade_offs: Optional[str] = None
    hard_constraints_satisfied: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class RecommendationOut(BaseModel):
    id: str
    business_id: str
    title: str
    action_type: str
    severity: str
    estimated_impact: float
    reasoning: str
    supporting_records: Optional[Dict[str, Any]] = None
    assumptions: Optional[str] = None
    disadvantages: Optional[str] = None
    status: RecommendationStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

@router.get("/{business_id}/goals", response_model=List[GoalOut])
def list_goals(
    business_id: str,
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db),
):
    return (
        db.query(FinancialGoal)
        .filter(FinancialGoal.business_id == business_id)
        .order_by(FinancialGoal.priority.asc())
        .all()
    )

@router.post("/{business_id}/goals", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
def create_or_update_goal(
    business_id: str,
    req: GoalCreate,
    membership: BusinessMembership = Depends(require_finance_or_higher),
    db: Session = Depends(get_db),
):
    return DecisionService.create_or_update_goal(
        db=db,
        business_id=business_id,
        name=req.name,
        goal_type=req.goal_type,
        target_amount=req.target_amount,
        target_date=req.target_date,
        is_hard_constraint=req.is_hard_constraint,
        priority=req.priority,
        notes=req.notes,
    )

@router.get("/{business_id}/scenarios", response_model=List[ScenarioOut])
def list_scenarios(
    business_id: str,
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db),
):
    scenarios = (
        db.query(SavedScenario)
        .filter(SavedScenario.business_id == business_id)
        .order_by(SavedScenario.created_at.desc())
        .all()
    )
    if not scenarios:
        # Create default baseline scenario
        baseline = DecisionService.evaluate_scenario(
            db=db,
            business_id=business_id,
            name="Baseline (Status Quo)",
            description="Historical run-rate with current collection velocity and no adjustments.",
            receivable_delay_days=0,
            collection_rate_pct=100.0,
            expense_multiplier=1.0,
            one_off_capex=0.0,
        )
        baseline.is_baseline = True
        db.commit()
        db.refresh(baseline)
        scenarios = [baseline]
    return scenarios

@router.post("/{business_id}/scenarios", response_model=ScenarioOut, status_code=status.HTTP_201_CREATED)
def create_scenario(
    business_id: str,
    req: ScenarioCreate,
    membership: BusinessMembership = Depends(require_finance_or_higher),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return DecisionService.evaluate_scenario(
        db=db,
        business_id=business_id,
        name=req.name,
        description=req.description,
        receivable_delay_days=req.receivable_delay_days,
        collection_rate_pct=req.collection_rate_pct,
        expense_multiplier=req.expense_multiplier,
        one_off_capex=req.one_off_capex,
        user_id=current_user.id,
    )

@router.post("/{business_id}/optimisation/run", response_model=OptimisationPlanOut)
def run_optimisation(
    business_id: str,
    scenario_id: Optional[str] = None,
    membership: BusinessMembership = Depends(require_finance_or_higher),
    db: Session = Depends(get_db),
):
    return DecisionService.run_decision_optimisation(
        db=db,
        business_id=business_id,
        scenario_id=scenario_id,
    )

@router.get("/{business_id}/recommendations", response_model=List[RecommendationOut])
def list_recommendations(
    business_id: str,
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db),
):
    recs = (
        db.query(FinancialRecommendation)
        .filter(FinancialRecommendation.business_id == business_id)
        .order_by(FinancialRecommendation.created_at.desc())
        .all()
    )
    if not recs:
        # Run optimization to populate recommendations
        DecisionService.run_decision_optimisation(db, business_id)
        recs = (
            db.query(FinancialRecommendation)
            .filter(FinancialRecommendation.business_id == business_id)
            .order_by(FinancialRecommendation.created_at.desc())
            .all()
        )
    return recs

@router.post("/{business_id}/recommendations/{rec_id}/status", response_model=RecommendationOut)
def update_recommendation_status(
    business_id: str,
    rec_id: str,
    status_update: str,  # "ACCEPTED" or "DISMISSED"
    membership: BusinessMembership = Depends(require_finance_or_higher),
    db: Session = Depends(get_db),
):
    rec = (
        db.query(FinancialRecommendation)
        .filter(FinancialRecommendation.business_id == business_id, FinancialRecommendation.id == rec_id)
        .first()
    )
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found.")

    if status_update == "ACCEPTED":
        rec.status = RecommendationStatus.ACCEPTED
    elif status_update == "DISMISSED":
        rec.status = RecommendationStatus.DISMISSED
    else:
        raise HTTPException(status_code=400, detail="Invalid status. Must be ACCEPTED or DISMISSED.")

    db.commit()
    db.refresh(rec)
    return rec

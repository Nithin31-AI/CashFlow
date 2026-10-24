from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_viewer_or_higher, require_accountant_or_higher
from app.models.membership import BusinessMembership
from app.models.simulation import SimulationRun
from app.services.simulation_service import SimulationService

router = APIRouter()

class SimulationRequest(BaseModel):
    horizon_days: int = Field(default=30, ge=7, le=365)
    num_paths: int = Field(default=1000, ge=100, le=5000)
    seed: Optional[int] = None
    custom_delay_days: Optional[int] = None
    collection_probability: float = Field(default=0.90, ge=0.1, le=1.0)
    expense_volatility_multiplier: float = Field(default=1.0, ge=0.5, le=3.0)

@router.post("/{business_id}/simulations/run", status_code=status.HTTP_201_CREATED)
def run_simulation(
    business_id: str,
    req: SimulationRequest,
    membership: BusinessMembership = Depends(require_accountant_or_higher),
    db: Session = Depends(get_db),
):
    try:
        run = SimulationService.run_monte_carlo(
            db=db,
            business_id=business_id,
            horizon_days=req.horizon_days,
            num_paths=req.num_paths,
            seed=req.seed,
            custom_delay_days=req.custom_delay_days,
            collection_probability=req.collection_probability,
            expense_volatility_multiplier=req.expense_volatility_multiplier,
        )
        return run
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{business_id}/simulations/latest")
def get_latest_simulation(
    business_id: str,
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db),
):
    run = (
        db.query(SimulationRun)
        .filter(SimulationRun.business_id == business_id)
        .order_by(SimulationRun.created_at.desc())
        .first()
    )
    if not run:
        # Run default 30-day baseline simulation
        run = SimulationService.run_monte_carlo(
            db=db,
            business_id=business_id,
            horizon_days=30,
            num_paths=1000,
            seed=42,
        )
    return run

@router.get("/{business_id}/simulations/{simulation_id}")
def get_simulation_by_id(
    business_id: str,
    simulation_id: str,
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db),
):
    run = (
        db.query(SimulationRun)
        .filter(SimulationRun.business_id == business_id, SimulationRun.id == simulation_id)
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="Simulation run not found.")
    return run

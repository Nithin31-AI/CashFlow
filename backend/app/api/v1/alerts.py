from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, field_validator
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_viewer_or_higher, require_finance_or_higher
from app.models.membership import BusinessMembership
from app.models.alert import AlertRule, AlertEvent, AlertCategory, AlertSeverity
from app.services.alert_service import AlertService

router = APIRouter()

class AlertRuleCreate(BaseModel):
    name: str
    category: AlertCategory
    threshold_value: Decimal
    severity: AlertSeverity = AlertSeverity.WARNING
    suppression_window_hours: int = 24
    is_active: bool = True

class AlertEventResponse(BaseModel):
    id: str
    business_id: str
    rule_id: Optional[str] = None
    title: str
    message: str
    category: str = "GENERAL"
    severity: AlertSeverity = AlertSeverity.WARNING
    financial_evidence: Optional[Dict[str, Any]] = None
    is_acknowledged: bool = False
    is_resolved: bool = False
    created_at: datetime

    @field_validator("category", mode="before")
    @classmethod
    def ensure_category_string(cls, v):
        if not v or not isinstance(v, str):
            return "GENERAL"
        return v

    model_config = {"from_attributes": True}

class EvaluateAlertsResponse(BaseModel):
    status: str
    triggered_count: int
    triggered_events: List[AlertEventResponse]

@router.get("/{business_id}/alerts/rules")
def list_alert_rules(
    business_id: str,
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db),
):
    rules = db.query(AlertRule).filter(AlertRule.business_id == business_id).all()
    if not rules:
        rules = AlertService.create_default_rules(db, business_id)
    return rules

@router.post("/{business_id}/alerts/rules", status_code=status.HTTP_201_CREATED)
def create_alert_rule(
    business_id: str,
    req: AlertRuleCreate,
    membership: BusinessMembership = Depends(require_finance_or_higher),
    db: Session = Depends(get_db),
):
    rule = AlertRule(
        business_id=business_id,
        name=req.name,
        category=req.category,
        threshold_value=req.threshold_value,
        severity=req.severity,
        suppression_window_hours=req.suppression_window_hours,
        is_active=req.is_active,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule

@router.get("/{business_id}/alerts/events", response_model=List[AlertEventResponse])
def list_alert_events(
    business_id: str,
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db),
):
    events = (
        db.query(AlertEvent)
        .filter(AlertEvent.business_id == business_id)
        .order_by(AlertEvent.created_at.desc())
        .all()
    )
    if not events:
        # Run alert evaluation to capture any active alerts
        events = AlertService.evaluate_rules_and_trigger(db, business_id)
    return events

@router.post("/{business_id}/alerts/evaluate", response_model=EvaluateAlertsResponse)
def evaluate_alerts(
    business_id: str,
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db),
):
    triggered = AlertService.evaluate_rules_and_trigger(db, business_id)
    return {"status": "SUCCESS", "triggered_count": len(triggered), "triggered_events": triggered}

@router.post("/{business_id}/alerts/events/{event_id}/acknowledge", response_model=AlertEventResponse)
def acknowledge_alert(
    business_id: str,
    event_id: str,
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db),
):
    ev = (
        db.query(AlertEvent)
        .filter(AlertEvent.business_id == business_id, AlertEvent.id == event_id)
        .first()
    )
    if not ev:
        raise HTTPException(status_code=404, detail="Alert event not found.")
    ev.is_acknowledged = True
    db.commit()
    return ev

@router.post("/{business_id}/alerts/events/{event_id}/resolve", response_model=AlertEventResponse)
def resolve_alert(
    business_id: str,
    event_id: str,
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db),
):
    ev = (
        db.query(AlertEvent)
        .filter(AlertEvent.business_id == business_id, AlertEvent.id == event_id)
        .first()
    )
    if not ev:
        raise HTTPException(status_code=404, detail="Alert event not found.")
    ev.is_resolved = True
    db.commit()
    return ev


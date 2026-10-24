from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import (
    get_db,
    require_finance_manager_or_higher,
)
from app.models.membership import BusinessMembership
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogOut

router = APIRouter()

@router.get("/{business_id}/audit-logs", response_model=List[AuditLogOut])
def get_business_audit_logs(
    business_id: str,
    membership: BusinessMembership = Depends(require_finance_manager_or_higher),
    db: Session = Depends(get_db)
):
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.business_id == business_id)
        .order_by(AuditLog.created_at.desc())
        .limit(100)
        .all()
    )
    return logs

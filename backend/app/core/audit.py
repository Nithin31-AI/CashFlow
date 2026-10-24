import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.audit import AuditLog

logger = logging.getLogger("cashflow.audit")

# Blacklisted keys that must never appear in audit details or logs
SENSITIVE_KEYS = {
    "password", "hashed_password", "token", "access_token", 
    "secret", "secret_key", "authorization", "raw_token"
}

def sanitize_details(data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not data or not isinstance(data, dict):
        return data
    sanitized = {}
    for k, v in data.items():
        if k.lower() in SENSITIVE_KEYS:
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_details(v)
        else:
            sanitized[k] = v
    return sanitized

def record_audit_log(
    db: Session,
    action: str,
    business_id: Optional[str] = None,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """
    Persists an audit event to the database and emits a structured log.
    Ensures zero sensitive credentials or passwords enter logs.
    """
    clean_details = sanitize_details(details)
    log_entry = AuditLog(
        business_id=business_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=clean_details,
        ip_address=ip_address,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    logger.info(
        "AUDIT: action=%s business_id=%s user_id=%s resource=%s/%s",
        action,
        business_id,
        user_id,
        resource_type,
        resource_id,
    )
    return log_entry

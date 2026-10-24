from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel

class AuditLogOut(BaseModel):
    id: str
    business_id: Optional[str] = None
    user_id: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

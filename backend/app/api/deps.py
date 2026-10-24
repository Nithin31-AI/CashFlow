from typing import Generator, List, Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.config import settings
from app.core.security import decode_access_token
from app.models.user import User
from app.models.membership import BusinessMembership, MembershipRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)

from app.db.session import get_db

def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or session has expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    jwt_token = token
    if not jwt_token and authorization and authorization.lower().startswith("bearer "):
        jwt_token = authorization.split(" ")[1]

    if not jwt_token:
        raise credentials_exception

    payload = decode_access_token(jwt_token)
    if not payload:
        raise credentials_exception

    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise credentials_exception

    return user

class RequireBusinessRole:
    """
    Validates that the authenticated user belongs to the specified business
    and possesses one of the required authorization roles.
    Never trusts client-supplied business ID without database verification.
    """
    def __init__(self, allowed_roles: List[MembershipRole]):
        self.allowed_roles = allowed_roles

    def __call__(
        self,
        business_id: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> BusinessMembership:
        membership = (
            db.query(BusinessMembership)
            .filter(
                BusinessMembership.business_id == business_id,
                BusinessMembership.user_id == current_user.id
            )
            .first()
        )

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not authorized to access this business."
            )

        if membership.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: Role '{membership.role.value}' cannot perform this operation. Required: {[r.value for r in self.allowed_roles]}."
            )

        return membership

# Role convenience dependencies
require_owner = RequireBusinessRole([MembershipRole.OWNER])
require_finance_manager_or_higher = RequireBusinessRole([MembershipRole.OWNER, MembershipRole.FINANCE_MANAGER])
require_finance_or_higher = require_finance_manager_or_higher
require_accountant_or_higher = RequireBusinessRole([
    MembershipRole.OWNER, 
    MembershipRole.FINANCE_MANAGER, 
    MembershipRole.ACCOUNTANT
])
require_viewer_or_higher = RequireBusinessRole([
    MembershipRole.OWNER, 
    MembershipRole.FINANCE_MANAGER, 
    MembershipRole.ACCOUNTANT, 
    MembershipRole.VIEWER
])

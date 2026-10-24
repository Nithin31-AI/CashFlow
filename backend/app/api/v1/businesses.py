import re
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, require_viewer_or_higher, require_owner
from app.core.audit import record_audit_log
from app.models.user import User
from app.models.business import Business
from app.models.membership import BusinessMembership, MembershipRole
from app.models.account import FinancialAccount, AccountType
from app.schemas.business import BusinessCreate, BusinessUpdate, BusinessOut

router = APIRouter()

def generate_slug(name: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    if not base:
        base = "business"
    return f"{base}-{uuid.uuid4().hex[:6]}"

@router.post("/", response_model=BusinessOut, status_code=status.HTTP_201_CREATED)
def create_business(
    req: BusinessCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    business = Business(
        name=req.name,
        slug=generate_slug(req.name),
        currency=req.currency.upper(),
        country=req.country.upper(),
        timezone=req.timezone,
    )
    db.add(business)
    db.flush()  # assign business.id

    # The user creating the business becomes its OWNER
    membership = BusinessMembership(
        business_id=business.id,
        user_id=current_user.id,
        role=MembershipRole.OWNER,
    )
    db.add(membership)

    # Automatically create a default Primary Bank Account for the business
    default_account = FinancialAccount(
        business_id=business.id,
        name="Operating Bank Account",
        account_type=AccountType.BANK,
        currency=business.currency,
        institution_name="Primary Bank",
        is_active=True,
    )
    db.add(default_account)
    db.commit()
    db.refresh(business)

    record_audit_log(
        db=db,
        action="BUSINESS_CREATED",
        business_id=business.id,
        user_id=current_user.id,
        resource_type="Business",
        resource_id=business.id,
        details={"name": business.name, "currency": business.currency},
        ip_address=request.client.host if request.client else None,
    )

    out = BusinessOut.model_validate(business)
    out.role = MembershipRole.OWNER.value
    return out

@router.get("/", response_model=List[BusinessOut])
def list_my_businesses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    memberships = (
        db.query(BusinessMembership)
        .filter(BusinessMembership.user_id == current_user.id)
        .all()
    )
    results = []
    for m in memberships:
        b = m.business
        out = BusinessOut.model_validate(b)
        out.role = m.role.value
        results.append(out)
    return results

@router.get("/{business_id}", response_model=BusinessOut)
def get_business(
    business_id: str,
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db)
):
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Business not found.")
    out = BusinessOut.model_validate(b)
    out.role = membership.role.value
    return out

@router.patch("/{business_id}", response_model=BusinessOut)
def update_business(
    business_id: str,
    req: BusinessUpdate,
    request: Request,
    membership: BusinessMembership = Depends(require_owner),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Business not found.")

    changes = {}
    if req.name is not None:
        changes["name"] = req.name
        b.name = req.name
    if req.currency is not None:
        changes["currency"] = req.currency.upper()
        b.currency = req.currency.upper()
    if req.country is not None:
        changes["country"] = req.country.upper()
        b.country = req.country.upper()
    if req.timezone is not None:
        changes["timezone"] = req.timezone
        b.timezone = req.timezone

    db.commit()
    db.refresh(b)

    record_audit_log(
        db=db,
        action="BUSINESS_UPDATED",
        business_id=b.id,
        user_id=current_user.id,
        resource_type="Business",
        resource_id=b.id,
        details=changes,
        ip_address=request.client.host if request.client else None,
    )

    out = BusinessOut.model_validate(b)
    out.role = membership.role.value
    return out

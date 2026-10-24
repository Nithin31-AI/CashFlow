from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.api.deps import (
    get_db,
    get_current_user,
    require_viewer_or_higher,
    require_owner,
)
from app.core.audit import record_audit_log
from app.models.user import User
from app.models.membership import BusinessMembership, MembershipRole
from app.schemas.membership import (
    MembershipInvite,
    MembershipUpdate,
    MembershipOut,
)

router = APIRouter()

@router.get("/{business_id}/members", response_model=List[MembershipOut])
def list_members(
    business_id: str,
    membership: BusinessMembership = Depends(require_viewer_or_higher),
    db: Session = Depends(get_db)
):
    members = (
        db.query(BusinessMembership)
        .filter(BusinessMembership.business_id == business_id)
        .all()
    )
    return members

@router.post("/{business_id}/members", response_model=MembershipOut, status_code=status.HTTP_201_CREATED)
def add_or_invite_member(
    business_id: str,
    req: MembershipInvite,
    request: Request,
    current_membership: BusinessMembership = Depends(require_owner),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_user = db.query(User).filter(User.email == req.email.lower()).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email '{req.email}' not found. They must first register for cashFlow."
        )

    existing = (
        db.query(BusinessMembership)
        .filter(
            BusinessMembership.business_id == business_id,
            BusinessMembership.user_id == target_user.id
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user is already a member of this business."
        )

    new_member = BusinessMembership(
        business_id=business_id,
        user_id=target_user.id,
        role=req.role,
    )
    db.add(new_member)
    db.commit()
    db.refresh(new_member)

    record_audit_log(
        db=db,
        action="MEMBER_ADDED",
        business_id=business_id,
        user_id=current_user.id,
        resource_type="BusinessMembership",
        resource_id=new_member.id,
        details={"invited_email": target_user.email, "role": req.role.value},
        ip_address=request.client.host if request.client else None,
    )

    return new_member

@router.patch("/{business_id}/members/{membership_id}", response_model=MembershipOut)
def update_member_role(
    business_id: str,
    membership_id: str,
    req: MembershipUpdate,
    request: Request,
    current_membership: BusinessMembership = Depends(require_owner),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target = (
        db.query(BusinessMembership)
        .filter(
            BusinessMembership.id == membership_id,
            BusinessMembership.business_id == business_id
        )
        .first()
    )
    if not target:
        raise HTTPException(status_code=404, detail="Membership not found.")

    # Guard: prevent removing the last owner
    if target.role == MembershipRole.OWNER and req.role != MembershipRole.OWNER:
        owner_count = (
            db.query(BusinessMembership)
            .filter(
                BusinessMembership.business_id == business_id,
                BusinessMembership.role == MembershipRole.OWNER
            )
            .count()
        )
        if owner_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the last remaining OWNER of the business."
            )

    old_role = target.role.value
    target.role = req.role
    db.commit()
    db.refresh(target)

    record_audit_log(
        db=db,
        action="MEMBER_ROLE_UPDATED",
        business_id=business_id,
        user_id=current_user.id,
        resource_type="BusinessMembership",
        resource_id=target.id,
        details={"target_user_id": target.user_id, "old_role": old_role, "new_role": req.role.value},
        ip_address=request.client.host if request.client else None,
    )

    return target

@router.delete("/{business_id}/members/{membership_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    business_id: str,
    membership_id: str,
    request: Request,
    current_membership: BusinessMembership = Depends(require_owner),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target = (
        db.query(BusinessMembership)
        .filter(
            BusinessMembership.id == membership_id,
            BusinessMembership.business_id == business_id
        )
        .first()
    )
    if not target:
        raise HTTPException(status_code=404, detail="Membership not found.")

    if target.role == MembershipRole.OWNER:
        owner_count = (
            db.query(BusinessMembership)
            .filter(
                BusinessMembership.business_id == business_id,
                BusinessMembership.role == MembershipRole.OWNER
            )
            .count()
        )
        if owner_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last remaining OWNER of the business."
            )

    target_email = target.user.email if target.user else target.user_id
    db.delete(target)
    db.commit()

    record_audit_log(
        db=db,
        action="MEMBER_REMOVED",
        business_id=business_id,
        user_id=current_user.id,
        resource_type="BusinessMembership",
        resource_id=membership_id,
        details={"removed_email": target_email},
        ip_address=request.client.host if request.client else None,
    )
    return None

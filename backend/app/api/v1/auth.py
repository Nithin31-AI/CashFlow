from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    generate_password_reset_token,
    hash_token,
)
from app.core.audit import record_audit_log
from app.models.user import User
from app.models.password_reset import PasswordResetToken
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    UserOut,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)

router = APIRouter()

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(req: UserRegister, request: Request, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address is already registered."
        )

    user = User(
        email=req.email.lower(),
        hashed_password=get_password_hash(req.password),
        full_name=req.full_name,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    record_audit_log(
        db=db,
        action="AUTH_REGISTER",
        user_id=user.id,
        resource_type="User",
        resource_id=user.id,
        details={"email": user.email},
        ip_address=request.client.host if request.client else None,
    )

    return user

@router.post("/login", response_model=Token)
def login(req: UserLogin, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email.lower()).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is deactivated."
        )

    access_token = create_access_token(subject=user.id)

    record_audit_log(
        db=db,
        action="AUTH_LOGIN",
        user_id=user.id,
        resource_type="User",
        resource_id=user.id,
        ip_address=request.client.host if request.client else None,
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserOut.model_validate(user),
    )

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(req: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    """
    Initiates password recovery. Does NOT reveal whether the email exists.
    Generates secure SHA-256 hashed reset token.
    """
    user = db.query(User).filter(User.email == req.email.lower()).first()
    dev_token = None

    if user and user.is_active:
        raw_token, token_hash = generate_password_reset_token()
        expires = datetime.now(timezone.utc) + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
        
        reset_entry = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires,
        )
        db.add(reset_entry)
        db.commit()

        record_audit_log(
            db=db,
            action="AUTH_FORGOT_PASSWORD_REQUESTED",
            user_id=user.id,
            resource_type="PasswordResetToken",
            ip_address=request.client.host if request.client else None,
        )

        if settings.DEV_MODE:
            dev_token = raw_token

    return ForgotPasswordResponse(
        message="If this email is registered in our system, password reset instructions have been generated.",
        dev_reset_token=dev_token,
    )

@router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password(req: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    """
    Resets password given a valid unexpired recovery token.
    """
    token_hash = hash_token(req.token)
    now = datetime.now(timezone.utc)

    reset_entry = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
        .first()
    )

    if not reset_entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The password reset link is invalid or has expired."
        )

    user = db.query(User).filter(User.id == reset_entry.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="Associated user not found.")

    user.hashed_password = get_password_hash(req.new_password)
    reset_entry.used_at = now
    db.commit()

    record_audit_log(
        db=db,
        action="AUTH_PASSWORD_RESET_COMPLETED",
        user_id=user.id,
        resource_type="User",
        resource_id=user.id,
        ip_address=request.client.host if request.client else None,
    )

    return ResetPasswordResponse(message="Your password has been successfully reset. You can now log in.")

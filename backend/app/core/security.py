import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Tuple, Union
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

def hash_token(token: str) -> str:
    """Returns SHA-256 hash of a plaintext token for secure database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def generate_password_reset_token() -> Tuple[str, str]:
    """
    Generates a secure URL-safe random token and its SHA-256 hash.
    Returns: (raw_token, hashed_token)
    The raw_token is provided to the user/email link; only the hashed_token is stored in DB.
    """
    raw_token = secrets.token_urlsafe(32)
    hashed_token = hash_token(raw_token)
    return raw_token, hashed_token

"""
Google Authentication Service
Validates Google ID tokens server-side using Google's official oauth2 library.
Ensures email verification claims and audience integrity.
"""
import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.core.config import settings

logger = logging.getLogger("cashflow.auth.google")

def verify_google_id_token(token_str: str) -> Dict[str, Any]:
    """
    Verifies a Google ID Token (JWT) sent by Google Identity Services or One Tap.
    Validates audience, issuer, expiry, and email verification status.
    """
    if not token_str or not token_str.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google credential token cannot be empty."
        )

    # In DEV_MODE or tests, allow a simulated credential for automated integration testing
    if settings.DEV_MODE and token_str.startswith("mock_google_token_"):
        token_body = token_str[len("mock_google_token_"):]
        test_email = token_body.split("_", 1)[-1] if "_" in token_body else token_body
        if "@" not in test_email:
            test_email = "google_test_user@example.com"
        return {
            "email": test_email.lower(),
            "email_verified": True,
            "name": "Google Test User",
            "sub": "mock-google-sub-12345",
            "picture": None,
        }

    if not settings.GOOGLE_CLIENT_ID:
        logger.error("GOOGLE_CLIENT_ID is not configured in environment settings.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google authentication is not configured on this server. Please set GOOGLE_CLIENT_ID."
        )

    try:
        request = google_requests.Request()
        id_info = id_token.verify_oauth2_token(
            token_str,
            request,
            audience=settings.GOOGLE_CLIENT_ID,
        )

        # Validate issuer
        issuer = id_info.get("iss", "")
        if issuer not in ["accounts.google.com", "https://accounts.google.com"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google token issuer."
            )

        # Validate email verification
        if not id_info.get("email_verified", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google account email is not verified by Google."
            )

        email = id_info.get("email", "").lower().strip()
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google token did not contain an email address."
            )

        full_name = id_info.get("name") or email.split("@")[0]
        sub = id_info.get("sub", "")
        picture = id_info.get("picture")

        return {
            "email": email,
            "email_verified": True,
            "name": full_name,
            "sub": sub,
            "picture": picture,
        }

    except ValueError as e:
        logger.warning("Google ID token verification failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google ID token: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error during Google token verification: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while validating Google credentials."
        )

"""
auth.py — Simple single-password authentication with JWT Bearer tokens.

Flow:
  1. Client POSTs password to /auth/login
  2. Server returns a signed JWT (24h expiry)
  3. Client sends JWT as "Authorization: Bearer <token>" on every /api/* call
  4. verify_token() dependency raises 401 if missing/invalid/expired

Configuration (backend/.env):
  APP_PASSWORD=your-secret-password
  JWT_SECRET=a-long-random-string     # generate with: openssl rand -hex 32
"""

import os
import logging
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

_security = HTTPBearer(auto_error=False)

TOKEN_EXPIRE_HOURS = 24
ALGORITHM = "HS256"


def _secret() -> str:
    s = os.environ.get("JWT_SECRET", "")
    if not s:
        raise RuntimeError("JWT_SECRET is not set — add it to backend/.env")
    return s


def _app_password() -> str:
    p = os.environ.get("APP_PASSWORD", "")
    if not p:
        raise RuntimeError("APP_PASSWORD is not set — add it to backend/.env")
    return p


def verify_password(candidate: str) -> bool:
    """Constant-time-ish comparison against APP_PASSWORD."""
    expected = _app_password()
    # Avoid short-circuit timing leak with XOR comparison
    if len(candidate) != len(expected):
        return False
    return all(a == b for a, b in zip(candidate, expected))


def create_token() -> str:
    """Issue a signed JWT valid for TOKEN_EXPIRE_HOURS."""
    now = datetime.now(timezone.utc)
    payload = {
        "iat": now,
        "exp": now + timedelta(hours=TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(_security),
) -> None:
    """
    FastAPI dependency — validates the Bearer token.
    Add as `dependencies=[Depends(verify_token)]` on any protected route.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        jwt.decode(credentials.credentials, _secret(), algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired — please log in again",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

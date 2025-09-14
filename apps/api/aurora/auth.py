from __future__ import annotations

from typing import Optional

from fastapi import Header, HTTPException, status
import jwt

from .config import settings


def _extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


def require_supabase_auth(authorization: Optional[str] = Header(None)) -> bool:
    """Authn guard for POST endpoints using Supabase JWT.
    If SUPABASE_JWT_SECRET is unset, this is a no-op to keep local/dev simple.
    """
    secret = getattr(settings, "supabase_jwt_secret", None)
    if not secret:
        return True
    token = _extract_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    try:
        # Supabase uses HS256 with the project's JWT secret
        jwt.decode(token, secret, algorithms=["HS256"], options={"verify_aud": False})
        return True
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# Lightweight RBAC roles via header for now: X-Role: admin|analyst|viewer
def require_role(role: str, x_role: Optional[str] = Header(None)) -> None:
    want = (role or "").lower()
    have = (x_role or "").lower()
    if not want or have == want:
        return
    # allow admin to pass any requirement
    if have == "admin":
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

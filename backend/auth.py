"""Admin authentication dependency for FastAPI."""
from fastapi import Depends, HTTPException, Request

from config import settings


def require_admin_token(request: Request) -> None:
    if not settings.admin_secret_token:
        raise HTTPException(status_code=503, detail="Admin not configured")
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer ") or auth[7:] != settings.admin_secret_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

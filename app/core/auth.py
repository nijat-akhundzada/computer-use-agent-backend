from fastapi import Header, HTTPException

from app.core.config import settings


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    api_key = (settings.API_KEY or "").strip()
    if not api_key:
        return

    if (x_api_key or "").strip() != api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

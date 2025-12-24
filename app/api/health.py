from fastapi import APIRouter

from app.core.redis import get_redis

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    r = get_redis()
    pong = r.ping()
    return {"ok": True, "redis": pong}

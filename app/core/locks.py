import uuid
from dataclasses import dataclass

from app.core.redis import get_redis


@dataclass
class LockHandle:
    key: str
    token: str


def acquire_session_lock(session_id: str, ttl_seconds: int = 120) -> LockHandle | None:
    """
    Simple Redis lock:
    SET key token NX EX ttl
    """
    r = get_redis()
    key = f"lock:session:{session_id}"
    token = str(uuid.uuid4())
    ok = r.set(key, token, nx=True, ex=ttl_seconds)
    if ok:
        return LockHandle(key=key, token=token)
    return None


def release_session_lock(handle: LockHandle) -> None:
    """
    Safe-ish unlock: delete only if token matches.
    Uses Lua to avoid deleting someone else's lock.
    """
    r = get_redis()
    script = """
    if redis.call("GET", KEYS[1]) == ARGV[1] then
      return redis.call("DEL", KEYS[1])
    else
      return 0
    end
    """
    r.eval(script, 1, handle.key, handle.token)

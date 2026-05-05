import json
from app.core.config import settings

_client = None


def _get_client():
    if not settings.REDIS_ENABLED:
        return None
    global _client
    if _client is None:
        import redis as redis_lib
        _client = redis_lib.from_url(settings.REDIS_URL, decode_responses=True)
    return _client


def cache_get(key: str):
    r = _get_client()
    if not r:
        return None
    try:
        val = r.get(key)
        return json.loads(val) if val else None
    except Exception:
        return None


def cache_set(key: str, value, ttl: int = 120):
    r = _get_client()
    if not r:
        return
    try:
        r.setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        pass


def cache_delete_pattern(pattern: str):
    r = _get_client()
    if not r:
        return
    try:
        keys = r.keys(pattern)
        if keys:
            r.delete(*keys)
    except Exception:
        pass

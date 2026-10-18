import json
import hashlib
from typing import Optional, Any
from app.config import settings

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

_client: Optional[Any] = None


async def get_redis():
    global _client
    if not settings.CACHE_ENABLED or not REDIS_AVAILABLE:
        return None
    if _client is None:
        _client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
    try:
        await _client.ping()
        return _client
    except Exception:
        return None


def _make_key(prefix: str, **params) -> str:
    raw = json.dumps(params, sort_keys=True)
    h = hashlib.md5(raw.encode()).hexdigest()[:12]
    return f"{prefix}:{h}"


async def cache_get(prefix: str, ttl: int = 300, **params) -> Optional[dict]:
    r = await get_redis()
    if r is None:
        return None
    key = _make_key(prefix, **params)
    val = await r.get(key)
    if val:
        return json.loads(val)
    return None


async def cache_set(prefix: str, data: Any, ttl: int = 300, **params):
    r = await get_redis()
    if r is None:
        return
    key = _make_key(prefix, **params)
    await r.setex(key, ttl, json.dumps(data, default=str))


async def cache_invalidate(prefix: str):
    r = await get_redis()
    if r is None:
        return
    cursor = 0
    while True:
        cursor, keys = await r.scan(cursor=cursor, match=f"{prefix}:*", count=100)
        if keys:
            await r.delete(*keys)
        if cursor == 0:
            break

import redis.asyncio as aioredis
from app.core.config import settings
from typing import Optional
import json

_redis: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def close_redis():
    global _redis
    if _redis:
        await _redis.close()
        _redis = None


# ─── Pub/Sub helpers for real-time TV updates ────────────────────────────────

MENU_UPDATE_CHANNEL = "menuvision:menu_updates"


async def publish_menu_update(restaurant_id: int, payload: dict):
    """Publish a menu update event to all subscribed TV clients."""
    r = await get_redis()
    message = json.dumps({"restaurant_id": restaurant_id, **payload})
    await r.publish(MENU_UPDATE_CHANNEL, message)


# ─── Cache helpers ────────────────────────────────────────────────────────────

async def cache_set(key: str, value: dict, ttl: int = 300):
    r = await get_redis()
    await r.setex(key, ttl, json.dumps(value))


async def cache_get(key: str) -> Optional[dict]:
    r = await get_redis()
    data = await r.get(key)
    return json.loads(data) if data else None


async def cache_delete(key: str):
    r = await get_redis()
    await r.delete(key)


async def cache_delete_pattern(pattern: str):
    r = await get_redis()
    keys = await r.keys(pattern)
    if keys:
        await r.delete(*keys)

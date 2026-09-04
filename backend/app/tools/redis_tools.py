import json
import time
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger
import redis.asyncio as aioredis

# Fallback in-memory cache and stream for local dev / tests when redis is offline
_IN_MEMORY_LOCKS = {}
_IN_MEMORY_STREAMS = []

_redis_client: Optional[aioredis.Redis] = None


async def get_redis_client() -> Optional[aioredis.Redis]:
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=1.5,
                socket_connect_timeout=1.5
            )
            # Ping test
            await _redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis not reachable ({str(e)}). Falling back to in-memory coordination.")
            _redis_client = None
    return _redis_client


async def acquire_lock_tool(lock_name: str, timeout_seconds: int = 10) -> bool:
    """Acquires a distributed lock."""
    client = await get_redis_client()
    if client:
        try:
            acquired = await client.set(f"lock:{lock_name}", "1", ex=timeout_seconds, nx=True)
            return bool(acquired)
        except Exception as e:
            logger.warning(f"Redis lock error: {str(e)}")

    # In-memory fallback
    now = time.time()
    if lock_name in _IN_MEMORY_LOCKS and _IN_MEMORY_LOCKS[lock_name] > now:
        return False
    _IN_MEMORY_LOCKS[lock_name] = now + timeout_seconds
    return True


async def release_lock_tool(lock_name: str) -> bool:
    """Releases a distributed lock."""
    client = await get_redis_client()
    if client:
        try:
            await client.delete(f"lock:{lock_name}")
            return True
        except Exception as e:
            logger.warning(f"Redis delete lock error: {str(e)}")

    _IN_MEMORY_LOCKS.pop(lock_name, None)
    return True


async def publish_event_tool(stream_name: str, event_data: Dict[str, Any]) -> str:
    """Publishes an event to Redis Stream and local in-memory timeline."""
    event_payload = {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in event_data.items()}
    client = await get_redis_client()
    if client:
        try:
            event_id = await client.xadd(stream_name, event_payload)
            return str(event_id)
        except Exception as e:
            logger.warning(f"Redis xadd error: {str(e)}")

    # In-memory stream
    in_mem_id = f"{int(time.time()*1000)}-{len(_IN_MEMORY_STREAMS)}"
    _IN_MEMORY_STREAMS.append({"id": in_mem_id, "stream": stream_name, "data": event_data})
    if len(_IN_MEMORY_STREAMS) > 1000:
        _IN_MEMORY_STREAMS.pop(0)
    return in_mem_id

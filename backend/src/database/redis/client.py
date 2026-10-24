"""Redis client management.

A single async client is shared per worker process. It is created lazily so
that importing the application (for example from Alembic or tests) does not
open sockets.
"""

import logging

from redis.asyncio import Redis

from src.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    _client: Redis | None = None

    @classmethod
    def get(cls) -> Redis:
        if cls._client is None:
            cls._client = Redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=settings.redis_max_connections,
                socket_timeout=settings.redis_socket_timeout_seconds,
                socket_connect_timeout=settings.redis_socket_timeout_seconds,
                health_check_interval=30,
            )
        return cls._client

    @classmethod
    async def close(cls) -> None:
        if cls._client is not None:
            try:
                await cls._client.aclose()
            except Exception:  # pragma: no cover - shutdown best effort
                logger.warning("Failed to close Redis connection", exc_info=True)
            finally:
                cls._client = None


async def get_redis_client() -> Redis:
    """FastAPI dependency returning the shared Redis client."""
    return RedisClient.get()

"""CRUD operations for anonymous short links stored in Redis.

Storage layout
--------------
``shortener:link:<code>``  -> JSON ``{url, created_at, expires_at}`` (with TTL)
``shortener:url:<sha256>`` -> ``<code>`` (with the same TTL, used for dedupe)

Both keys expire together, which guarantees that the URL index never points at
a link that no longer exists.
"""

import json
import logging
from datetime import datetime, timedelta, timezone

from redis.asyncio import Redis

from src.utils.hashing import sha256_hex

logger = logging.getLogger(__name__)

LINK_KEY_PREFIX = "shortener:link:"
URL_INDEX_PREFIX = "shortener:url:"


class RedisLinkStore:
    def __init__(self, client: Redis) -> None:
        self.client = client

    # ------------------------------------------------------------- keys
    @staticmethod
    def _link_key(code: str) -> str:
        return f"{LINK_KEY_PREFIX}{code}"

    @staticmethod
    def _url_key(normalized_url: str) -> str:
        return f"{URL_INDEX_PREFIX}{sha256_hex(normalized_url)}"

    # -------------------------------------------------------------- read
    async def get(self, code: str) -> dict | None:
        raw = await self.client.get(self._link_key(code))
        if raw is None:
            return None
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Corrupted Redis payload for code %s, deleting", code)
            await self.delete(code)
            return None
        if not isinstance(data, dict) or "url" not in data:
            return None
        return data

    async def find_code_by_url(self, normalized_url: str) -> str | None:
        return await self.client.get(self._url_key(normalized_url))

    async def exists(self, code: str) -> bool:
        return bool(await self.client.exists(self._link_key(code)))

    # ------------------------------------------------------------- write
    async def save_if_absent(
        self, code: str, normalized_url: str, ttl_seconds: int
    ) -> str:
        """Store a link unless the same URL already exists.

        Returns the code that is actually stored: either ``code`` for a new
        link or the code of the previously created link. This implements
        business rule #2 atomically enough for concurrent requests.
        """
        url_key = self._url_key(normalized_url)
        now = datetime.now(timezone.utc)
        payload = json.dumps(
            {
                "url": normalized_url,
                "created_at": now.isoformat(),
                "expires_at": (
                    now + timedelta(seconds=ttl_seconds)
                ).isoformat(),
            }
        )

        for _ in range(3):
            existing_code = await self.client.get(url_key)
            if existing_code:
                # Drop a stale index entry whose link expired between reads.
                if await self.exists(existing_code):
                    return existing_code
                await self.client.delete(url_key)

            # Reserve the URL -> code mapping first (atomic SET NX).
            if await self.client.set(url_key, code, ex=ttl_seconds, nx=True):
                await self.client.set(
                    self._link_key(code), payload, ex=ttl_seconds
                )
                return code

        # Extremely unlikely: keep fighting with concurrent writers.
        raise RuntimeError("Could not reserve a short code in Redis")

    async def delete(self, code: str) -> None:
        data = await self.get(code)
        keys = [self._link_key(code)]
        if data:
            keys.append(self._url_key(data["url"]))
        await self.client.delete(*keys)

    # -------------------------------------------------------------- misc
    async def ping(self) -> bool:
        return bool(await self.client.ping())

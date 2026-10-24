"""Rate limiting configuration (slowapi + Redis storage).

The limiter is shared by every API worker through Redis, so the quota is
global across replicas rather than per-process. Authenticated requests are
keyed by a hash of the bearer token, anonymous ones by client IP.
"""

import logging

from fastapi import Request
from slowapi import Limiter

from src.config import settings
from src.utils.hashing import hash_token
from src.utils.request import get_client_ip

logger = logging.getLogger(__name__)


def rate_limit_key(request: Request) -> str:
    authorization = request.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        return f"token:{hash_token(authorization[7:].strip())}"
    return f"ip:{get_client_ip(request)}"


def _build_limiter() -> Limiter:
    if not settings.rate_limit_enabled:
        # ``enabled=False`` still keeps decorators valid while disabling checks.
        return Limiter(key_func=rate_limit_key, enabled=False)
    try:
        return Limiter(
            key_func=rate_limit_key,
            storage_uri=settings.rate_limit_storage_uri,
            strategy="fixed-window",
            default_limits=[],
        )
    except Exception:  # pragma: no cover - fall back to in-memory storage
        logger.exception(
            "Could not initialise Redis rate-limit storage, using memory storage"
        )
        return Limiter(
            key_func=rate_limit_key,
            storage_uri="memory://",
            strategy="fixed-window",
            default_limits=[],
        )


limiter = _build_limiter()

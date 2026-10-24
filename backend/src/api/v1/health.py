"""Infrastructure health check used by Docker / Compose."""

import json
import logging
import os

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from src.api.deps import RedisDep, SessionDep

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health", include_in_schema=False)
async def health(session: SessionDep, redis: RedisDep) -> Response:
    try:
        await session.execute(text("SELECT 1"))
        await redis.ping()
    except Exception as exc:  # pragma: no cover - depends on infra state
        logger.error("Health check failed: %s", exc)
        return Response(
            content='{"status":"unhealthy"}',
            media_type="application/json",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return Response(
        content=json.dumps(
            {"status": "ok", "instance": os.getenv("HOSTNAME", "backend")}
        ),
        media_type="application/json",
    )

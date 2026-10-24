"""FastAPI application entry point."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.extension import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware

from src.api.redirect import router as redirect_router
from src.api.v1 import api_router
from src.config import settings
from src.database.postgre.session import dispose_engine
from src.database.redis.client import RedisClient
from src.utils.rate_limit import limiter

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Compose waits for Redis/PostgreSQL health, but never crash the whole API
    # for a transient dependency hiccup: individual endpoints degrade instead.
    try:
        await RedisClient.get().ping()
        logger.info("Connected to Redis")
    except Exception:  # pragma: no cover - startup diagnostics only
        logger.exception("Redis is not reachable at startup")

    yield

    await RedisClient.close()
    await dispose_engine()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "URL shortener with anonymous links stored in Redis, authenticated "
        "links and analytics in PostgreSQL, QR codes and rate limiting."
    ),
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)
app.include_router(redirect_router)

INSTANCE_ID = os.getenv("HOSTNAME", "backend")


@app.middleware("http")
async def add_instance_header(request, call_next):
    """Expose the replica name so load balancing is easy to verify:
    ``curl -sI http://localhost:8080/api/v1/health | grep X-Instance``."""
    response = await call_next(request)
    response.headers["X-Instance"] = INSTANCE_ID
    return response


@app.get("/api", include_in_schema=False)
async def api_root() -> dict:
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": f"{settings.api_v1_prefix}/health",
    }

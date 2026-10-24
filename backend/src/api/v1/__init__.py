"""API v1 router aggregation."""

from fastapi import APIRouter

from src.api.v1 import auth, health, links, stats

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(links.router)
api_router.include_router(stats.router)

__all__ = ["api_router"]

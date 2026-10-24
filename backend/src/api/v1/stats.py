"""Analytics endpoints for authenticated users."""

import logging

from fastapi import APIRouter, Query

from src.api.deps import CurrentUser, StatsServiceDep
from src.schemas.stats import LinkStatsResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stats", tags=["stats"])


@router.get(
    "/{short_code}",
    response_model=LinkStatsResponse,
    summary="Clicks, timestamps and referers for one of your links",
)
async def link_stats(
    short_code: str,
    user: CurrentUser,
    service: StatsServiceDep,
    limit: int = Query(default=200, ge=1, le=1000),
) -> LinkStatsResponse:
    return await service.get_stats(short_code, user, limit=limit)

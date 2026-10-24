"""Short link endpoints (creation, listing, deletion, QR)."""

import logging

from fastapi import APIRouter, Query, Request, Response, status

from src.api.deps import CurrentUser, LinkServiceDep, OptionalUser
from src.config import settings
from src.schemas.link import LinkCreate, LinkListResponse, LinkResponse
from src.service.link_service import build_short_url
from src.utils.qr import generate_qr_svg
from src.utils.rate_limit import limiter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/links", tags=["links"])


@router.post(
    "",
    response_model=LinkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a short link (anonymous or authenticated)",
)
@limiter.limit(settings.link_creation_rate_limit)
async def create_link(
    request: Request,
    payload: LinkCreate,
    user: OptionalUser,
    service: LinkServiceDep,
) -> LinkResponse:
    """Anonymous calls are stored in Redis with a fixed TTL.

    For anonymous users the ``ttl_seconds`` field is ignored by design.
    Authenticated calls are stored in PostgreSQL and honour ``ttl_seconds``
    (``null`` = never expires).
    """
    return await service.create_link(payload, user)


@router.get(
    "",
    response_model=LinkListResponse,
    summary="List links of the authenticated user",
)
async def list_links(
    user: CurrentUser,
    service: LinkServiceDep,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> LinkListResponse:
    items, total = await service.list_links(user, limit=limit, offset=offset)
    return LinkListResponse(
        items=items, total=total, limit=limit, offset=offset
    )


@router.delete(
    "/{short_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete one of your links",
)
async def delete_link(
    short_code: str,
    user: CurrentUser,
    service: LinkServiceDep,
) -> Response:
    await service.delete_link(short_code, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{short_code}/qr",
    response_class=Response,
    responses={200: {"content": {"image/svg+xml": {}}}},
    summary="QR code for a short link (SVG)",
)
async def link_qr(short_code: str) -> Response:
    svg = generate_qr_svg(build_short_url(short_code))
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=86400"},
    )

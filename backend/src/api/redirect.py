"""Public redirect endpoint.

The production Nginx config proxies ``/l/<code>`` straight to the backends.
"""

import logging

from fastapi import APIRouter, BackgroundTasks, Request, status
from fastapi.responses import RedirectResponse

from src.api.deps import LinkServiceDep
from src.service.link_service import record_click
from src.utils.request import get_client_ip

logger = logging.getLogger(__name__)
router = APIRouter(tags=["redirect"], include_in_schema=False)


@router.get("/l/{short_code}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def redirect_short_link(
    short_code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    service: LinkServiceDep,
) -> RedirectResponse:
    target_url, is_persistent = await service.resolve_short_code(short_code)
    if is_persistent:
        background_tasks.add_task(
            record_click,
            short_code,
            request.headers.get("referer"),
            request.headers.get("user-agent"),
            get_client_ip(request),
        )
    return RedirectResponse(
        url=target_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT
    )

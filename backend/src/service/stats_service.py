"""Analytics for authenticated users."""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models.user import User
from src.repository.click_repository import ClickRepository
from src.repository.link_repository import LinkRepository
from src.schemas.stats import ClickOut, LinkStatsResponse
from src.service.link_service import build_short_url


class StatsService:
    def __init__(
        self,
        session: AsyncSession,
        link_repository: LinkRepository,
        click_repository: ClickRepository,
    ) -> None:
        self.session = session
        self.links = link_repository
        self.clicks = click_repository

    async def get_stats(
        self, short_code: str, user: User, limit: int | None = None
    ) -> LinkStatsResponse:
        link = await self.links.get_by_short_code(short_code)
        if link is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Short link not found",
            )
        if link.owner_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this link's statistics",
            )

        page_size = min(limit or settings.stats_clicks_page_size, 1000)
        clicks = await self.clicks.list_for_link(link.id, limit=page_size)
        total = await self.clicks.count_for_link(link.id)
        last_clicked_at = await self.clicks.last_click_at(link.id)

        return LinkStatsResponse(
            short_code=link.short_code,
            short_url=build_short_url(link.short_code),
            original_url=link.original_url,
            created_at=link.created_at,
            expires_at=link.expires_at,
            total_clicks=total,
            last_clicked_at=last_clicked_at,
            clicks=[
                ClickOut(
                    clicked_at=click.clicked_at,
                    referer=click.referer,
                    referer_source=click.referer_source,
                    user_agent=click.user_agent,
                    ip_address=click.ip_address,
                )
                for click in clicks
            ],
        )

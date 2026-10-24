"""Short link persistence (PostgreSQL, authenticated users only)."""

import uuid
from datetime import datetime

from sqlalchemy import func, select

from src.database.postgre.crud import CrudRepository
from src.models.click import Click
from src.models.link import Link


class LinkRepository(CrudRepository[Link]):
    model = Link

    async def get_by_short_code(self, short_code: str) -> Link | None:
        stmt = select(Link).where(Link.short_code == short_code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def code_exists(self, short_code: str) -> bool:
        stmt = select(Link.id).where(Link.short_code == short_code).limit(1)
        return (await self.session.execute(stmt)).scalar_one_or_none() is not None

    async def create(
        self,
        *,
        short_code: str,
        original_url: str,
        owner_id: uuid.UUID,
        expires_at: datetime | None,
    ) -> Link:
        link = Link(
            short_code=short_code,
            original_url=original_url,
            owner_id=owner_id,
            expires_at=expires_at,
        )
        self.add(link)
        await self.session.flush()
        return link

    async def list_by_owner_with_clicks(
        self, owner_id: uuid.UUID, limit: int, offset: int
    ) -> list[tuple[Link, int]]:
        clicks_count = func.count(Click.id).label("clicks_count")
        stmt = (
            select(Link, clicks_count)
            .outerjoin(Click, Click.link_id == Link.id)
            .where(Link.owner_id == owner_id)
            .group_by(Link.id)
            .order_by(Link.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return [(row[0], int(row[1])) for row in result.all()]

    async def count_by_owner(self, owner_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(Link)
            .where(Link.owner_id == owner_id)
        )
        return int((await self.session.execute(stmt)).scalar_one())

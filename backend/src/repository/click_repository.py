"""Click event persistence and aggregation."""

import uuid

from sqlalchemy import func, select

from src.database.postgre.crud import CrudRepository
from src.models.click import Click


class ClickRepository(CrudRepository[Click]):
    model = Click

    async def add_click(
        self,
        *,
        link_id: uuid.UUID,
        referer: str | None,
        referer_source: str | None,
        user_agent: str | None,
        ip_address: str | None,
    ) -> Click:
        click = Click(
            link_id=link_id,
            referer=referer,
            referer_source=referer_source,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self.add(click)
        await self.session.flush()
        return click

    async def list_for_link(
        self, link_id: uuid.UUID, limit: int = 200, offset: int = 0
    ) -> list[Click]:
        stmt = (
            select(Click)
            .where(Click.link_id == link_id)
            .order_by(Click.clicked_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_for_link(self, link_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(Click)
            .where(Click.link_id == link_id)
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def last_click_at(self, link_id: uuid.UUID):
        stmt = select(func.max(Click.clicked_at)).where(Click.link_id == link_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

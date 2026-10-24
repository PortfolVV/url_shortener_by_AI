"""Small, generic CRUD helpers reused by the repository layer.

The repository layer (:mod:`src.repository`) owns the domain-specific
queries; this module only removes boilerplate such as "get by primary key",
"add and flush" and "delete".
"""

from typing import Any, Generic, Sequence, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.postgre.base_class import Base

ModelType = TypeVar("ModelType", bound=Base)


class CrudRepository(Generic[ModelType]):
    model: type[ModelType]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, ident: Any) -> ModelType | None:
        return await self.session.get(self.model, ident)

    async def list(self, limit: int = 100, offset: int = 0) -> Sequence[ModelType]:
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    def add(self, obj: ModelType) -> ModelType:
        self.session.add(obj)
        return obj

    async def add_and_flush(self, obj: ModelType) -> ModelType:
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def delete(self, obj: ModelType) -> None:
        await self.session.delete(obj)

    async def count(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(self.model)
        )
        return int(result.scalar_one())

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

"""User persistence."""

from sqlalchemy import select

from src.database.postgre.crud import CrudRepository
from src.models.user import User


class UserRepository(CrudRepository[User]):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, email: str, hashed_password: str) -> User:
        user = User(email=email.lower(), hashed_password=hashed_password)
        self.add(user)
        await self.session.flush()
        return user

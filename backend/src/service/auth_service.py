"""Business logic for registration, login and token issuance."""

import asyncio
import logging
import uuid
from datetime import timedelta
from functools import lru_cache

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from src.config import settings
from src.models.user import User
from src.repository.user_repository import UserRepository
from src.schemas.auth import TokenResponse, UserCreate, UserLogin, UserOut
from src.utils.security import (
    create_access_token,
    hash_password,
    verify_password,
)

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _dummy_password_hash() -> str:
    """A real bcrypt hash used to keep failed-login timing constant."""
    return hash_password("timing-protection-dummy-password")


class AuthService:
    def __init__(self, session, users: UserRepository) -> None:
        self.session = session
        self.users = users

    async def register(self, payload: UserCreate) -> User:
        email = payload.email.lower()
        if await self.users.get_by_email(email) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists",
            )

        # bcrypt is CPU-bound; keep the event loop responsive.
        hashed_password = await asyncio.to_thread(
            hash_password, payload.password
        )
        try:
            user = await self.users.create(
                email=email, hashed_password=hashed_password
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            logger.info("Concurrent registration for %s", email)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists",
            ) from exc
        await self.session.refresh(user)
        return user

    async def authenticate(self, payload: UserLogin) -> User:
        user = await self.users.get_by_email(payload.email.lower())
        if user is None:
            # Always run a hash comparison to keep timing roughly constant.
            await asyncio.to_thread(
                verify_password,
                payload.password,
                _dummy_password_hash(),
            )
            raise self._invalid_credentials()

        is_valid = await asyncio.to_thread(
            verify_password, payload.password, user.hashed_password
        )
        if not is_valid:
            raise self._invalid_credentials()
        return user

    async def login(self, payload: UserLogin) -> TokenResponse:
        user = await self.authenticate(payload)
        token = create_access_token(
            subject=str(user.id),
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        )
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserOut.model_validate(user),
        )

    async def get_user(self, user_id: uuid.UUID) -> User | None:
        return await self.users.get(user_id)

    @staticmethod
    def _invalid_credentials() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

"""Shared FastAPI dependencies and type aliases."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.postgre.session import get_session
from src.database.redis.client import get_redis_client
from src.database.redis.crud import RedisLinkStore
from src.models.user import User
from src.repository.click_repository import ClickRepository
from src.repository.link_repository import LinkRepository
from src.repository.user_repository import UserRepository
from src.service.auth_service import AuthService
from src.service.link_service import LinkService
from src.service.stats_service import StatsService
from src.utils.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

SessionDep = Annotated[AsyncSession, Depends(get_session)]
RedisDep = Annotated[Redis, Depends(get_redis_client)]


async def _resolve_user(
    credentials: HTTPAuthorizationCredentials | None,
    session: AsyncSession,
) -> User | None:
    if credentials is None:
        return None
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise CREDENTIALS_EXCEPTION
    try:
        user_id = payload["sub"]
        import uuid

        parsed_id = uuid.UUID(user_id)
    except (KeyError, ValueError) as exc:
        raise CREDENTIALS_EXCEPTION from exc
    user = await UserRepository(session).get(parsed_id)
    if user is None:
        raise CREDENTIALS_EXCEPTION
    return user


async def get_optional_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
    session: SessionDep,
) -> User | None:
    """Return the user for a valid bearer token, ``None`` for anonymous calls."""
    return await _resolve_user(credentials, session)


async def get_current_user(
    user: Annotated[User | None, Depends(get_optional_user)],
) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(session=session, users=UserRepository(session))


async def get_link_service(
    session: SessionDep, redis: RedisDep
) -> LinkService:
    redis_client: Redis = redis
    return LinkService(
        session=session,
        link_repository=LinkRepository(session),
        click_repository=ClickRepository(session),
        redis_store=RedisLinkStore(redis_client),
    )


async def get_stats_service(session: SessionDep) -> StatsService:
    return StatsService(
        session=session,
        link_repository=LinkRepository(session),
        click_repository=ClickRepository(session),
    )


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
LinkServiceDep = Annotated[LinkService, Depends(get_link_service)]
StatsServiceDep = Annotated[StatsService, Depends(get_stats_service)]

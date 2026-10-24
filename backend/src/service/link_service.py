"""Core link business logic.

This module is the heart of the application and implements the two strict
storage rules:

* authenticated user links  -> PostgreSQL only;
* anonymous user links      -> Redis only, with a fixed TTL, deduplicated by
  the original URL so that shortening the same URL twice returns the *same*
  short code.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

from fastapi import HTTPException, status
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database.postgre.session import AsyncSessionLocal
from src.database.redis.crud import RedisLinkStore
from src.models.click import Click
from src.models.link import Link
from src.models.user import User
from src.repository.click_repository import ClickRepository
from src.repository.link_repository import LinkRepository
from src.schemas.link import LinkCreate, LinkResponse
from src.utils.hashing import generate_short_code
from src.utils.qr import generate_qr_data_uri
from src.utils.url_validator import validate_and_normalize_url

logger = logging.getLogger(__name__)


def build_short_url(short_code: str) -> str:
    return f"{settings.base_url.rstrip('/')}/l/{short_code}"


def extract_referer_source(referer: str | None) -> str:
    """Reduce a Referer header to its host; "direct" when absent."""
    if not referer:
        return "direct"
    try:
        host = urlsplit(referer).hostname
    except ValueError:
        return "unknown"
    return (host or "direct")[:255]


class LinkService:
    def __init__(
        self,
        session: AsyncSession,
        link_repository: LinkRepository,
        click_repository: ClickRepository,
        redis_store: RedisLinkStore,
    ) -> None:
        self.session = session
        self.links = link_repository
        self.clicks = click_repository
        self.redis = redis_store

    # ------------------------------------------------------------- create
    async def create_link(
        self, payload: LinkCreate, user: User | None
    ) -> LinkResponse:
        normalized_url = await validate_and_normalize_url(payload.original_url)
        if user is None:
            return await self._create_anonymous_link(normalized_url)
        return await self._create_user_link(
            normalized_url, user, payload.ttl_seconds
        )

    async def _create_user_link(
        self, normalized_url: str, user: User, ttl_seconds: int | None
    ) -> LinkResponse:
        expires_at = (
            datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
            if ttl_seconds is not None
            else None
        )
        short_code = await self._generate_unique_code()

        try:
            link = await self.links.create(
                short_code=short_code,
                original_url=normalized_url,
                owner_id=user.id,
                expires_at=expires_at,
            )
            await self.session.commit()
            await self.session.refresh(link)
        except Exception:
            await self.session.rollback()
            logger.exception("Failed to persist link for user %s", user.id)
            raise

        qr_code = await asyncio.to_thread(
            generate_qr_data_uri, build_short_url(link.short_code)
        )
        return self._link_to_response(link, qr_code=qr_code)

    async def _create_anonymous_link(
        self, normalized_url: str
    ) -> LinkResponse:
        ttl_seconds = settings.anonymous_link_ttl_seconds
        try:
            existing_code = await self.redis.find_code_by_url(normalized_url)
            if existing_code:
                existing = await self.redis.get(existing_code)
                if existing is not None:
                    # Business rule #2: return the already existing short link.
                    return await self._redis_payload_to_response(
                        existing_code, existing, reused=True
                    )

            short_code = await self._generate_unique_code()
            stored_code = await self.redis.save_if_absent(
                short_code, normalized_url, ttl_seconds
            )
            payload = await self.redis.get(stored_code)
            if payload is None:  # pragma: no cover - Redis anomaly
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Link storage is temporarily unavailable",
                )
            return await self._redis_payload_to_response(
                stored_code, payload, reused=stored_code != short_code
            )
        except RedisError as exc:
            logger.exception("Redis failure while creating anonymous link")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Link storage is temporarily unavailable",
            ) from exc

    async def _generate_unique_code(self) -> str:
        for _ in range(settings.short_code_max_attempts):
            code = generate_short_code(settings.short_code_length)
            try:
                if await self.redis.exists(code):
                    continue
            except RedisError:
                # A Redis outage must not prevent authenticated links from
                # being created in PostgreSQL; collision odds are negligible.
                logger.warning("Redis unavailable during code collision check")
            if await self.links.code_exists(code):
                continue
            return code
        logger.error("Could not generate a unique short code")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not allocate a short code, please retry",
        )

    # ------------------------------------------------------------- resolve
    async def resolve_short_code(self, short_code: str) -> tuple[str, bool]:
        """Return ``(target_url, is_persistent)`` for a redirect.

        ``is_persistent`` tells the caller whether click statistics should be
        recorded (only PostgreSQL-backed links have analytics).
        """
        if not 4 <= len(short_code) <= 32:
            raise self._not_found()

        try:
            data = await self.redis.get(short_code)
        except RedisError:
            # Redis being down must not break links owned by users.
            logger.warning("Redis unavailable during redirect lookup")
            data = None

        if data is not None:
            return data["url"], False

        link = await self.links.get_by_short_code(short_code)
        if link is None:
            raise self._not_found()
        if not link.is_active:
            raise self._gone("Short link is no longer active")
        if link.expires_at is not None and link.expires_at <= datetime.now(
            timezone.utc
        ):
            raise self._gone("Short link has expired")
        return link.original_url, True

    # ---------------------------------------------------------------- list
    async def list_links(
        self, user: User, limit: int, offset: int
    ) -> tuple[list[LinkResponse], int]:
        rows = await self.links.list_by_owner_with_clicks(
            user.id, limit=limit, offset=offset
        )
        total = await self.links.count_by_owner(user.id)
        items = [
            self._link_to_response(link, clicks_count=clicks)
            for link, clicks in rows
        ]
        return items, total

    async def delete_link(self, short_code: str, user: User) -> None:
        link = await self.links.get_by_short_code(short_code)
        if link is None:
            raise self._not_found()
        if link.owner_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this link",
            )
        await self.links.delete(link)
        await self.session.commit()

    # ------------------------------------------------------------- helpers
    def _link_to_response(
        self,
        link: Link,
        *,
        qr_code: str | None = None,
        clicks_count: int | None = None,
    ) -> LinkResponse:
        return LinkResponse(
            short_code=link.short_code,
            short_url=build_short_url(link.short_code),
            original_url=link.original_url,
            created_at=link.created_at,
            expires_at=link.expires_at,
            qr_code=qr_code,
            is_authenticated=True,
            reused=False,
            clicks_count=clicks_count,
        )

    async def _redis_payload_to_response(
        self, short_code: str, payload: dict, *, reused: bool
    ) -> LinkResponse:
        short_url = build_short_url(short_code)
        qr_code = await asyncio.to_thread(generate_qr_data_uri, short_url)
        return LinkResponse(
            short_code=short_code,
            short_url=short_url,
            original_url=payload["url"],
            created_at=self._parse_datetime(payload.get("created_at")),
            expires_at=self._parse_datetime(payload.get("expires_at")),
            qr_code=qr_code,
            is_authenticated=False,
            reused=reused,
        )

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime:
        if not value:
            return datetime.now(timezone.utc)
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return datetime.now(timezone.utc)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

    @staticmethod
    def _not_found() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short link not found",
        )

    @staticmethod
    def _gone(detail: str) -> HTTPException:
        return HTTPException(status_code=status.HTTP_410_GONE, detail=detail)


async def record_click(
    short_code: str,
    referer: str | None,
    user_agent: str | None,
    ip_address: str | None,
) -> None:
    """Persist a click for a PostgreSQL-backed link.

    Runs as a Starlette background task with its own session, because the
    request-scoped session is already being torn down by the time it executes.
    Anonymous (Redis-only) links intentionally produce no analytics.
    """
    try:
        async with AsyncSessionLocal() as session:
            links = LinkRepository(session)
            link = await links.get_by_short_code(short_code)
            if link is None:
                return
            session.add(
                Click(
                    link_id=link.id,
                    referer=(referer or "")[:4096] or None,
                    referer_source=extract_referer_source(referer),
                    user_agent=(user_agent or "")[:1024] or None,
                    ip_address=(ip_address or "")[:64] or None,
                )
            )
            await session.commit()
    except Exception:  # pragma: no cover - never break the redirect
        logger.exception("Failed to record click for %s", short_code)

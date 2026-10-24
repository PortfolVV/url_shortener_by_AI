"""Pydantic schemas for short links."""

from datetime import datetime

from pydantic import BaseModel, Field

MIN_TTL_SECONDS = 60
MAX_TTL_SECONDS = 60 * 60 * 24 * 365  # 1 year


class LinkCreate(BaseModel):
    original_url: str = Field(
        min_length=3,
        max_length=2048,
        examples=["https://example.com/some/long/path"],
    )
    # ``None`` means "forever" for authenticated users. The value is ignored
    # for anonymous users, whose links always get the fixed Redis TTL.
    ttl_seconds: int | None = Field(
        default=None,
        ge=MIN_TTL_SECONDS,
        le=MAX_TTL_SECONDS,
        description="Link lifetime in seconds; null means no expiration.",
        examples=[86400],
    )


class LinkResponse(BaseModel):
    short_code: str
    short_url: str
    original_url: str
    created_at: datetime
    expires_at: datetime | None = None
    qr_code: str | None = Field(
        default=None,
        description="SVG QR code as a data URI (returned on creation).",
    )
    is_authenticated: bool = False
    reused: bool = Field(
        default=False,
        description="True when an existing anonymous link was returned instead of a new one.",
    )
    clicks_count: int | None = None


class LinkListResponse(BaseModel):
    items: list[LinkResponse]
    total: int
    limit: int
    offset: int

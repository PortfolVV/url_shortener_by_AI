"""Pydantic schemas for analytics."""

from datetime import datetime

from pydantic import BaseModel


class ClickOut(BaseModel):
    clicked_at: datetime
    referer: str | None = None
    referer_source: str | None = None
    user_agent: str | None = None
    ip_address: str | None = None


class LinkStatsResponse(BaseModel):
    short_code: str
    short_url: str
    original_url: str
    created_at: datetime
    expires_at: datetime | None = None
    total_clicks: int
    last_clicked_at: datetime | None = None
    clicks: list[ClickOut]

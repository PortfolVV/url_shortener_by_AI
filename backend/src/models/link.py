"""Short link model.

Only links that belong to a registered user are persisted here. Anonymous
links live exclusively in Redis (business rule #1) and are never written to
PostgreSQL (business rule #5).
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, func, true
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.postgre.base_class import Base

if TYPE_CHECKING:  # pragma: no cover
    from src.models.click import Click
    from src.models.user import User


class Link(Base):
    __tablename__ = "links"
    __table_args__ = (
        # Covers "my links" listings filtered by owner and ordered by date.
        Index("ix_links_owner_id_created_at", "owner_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    short_code: Mapped[str] = mapped_column(
        String(16), unique=True, index=True, nullable=False
    )
    original_url: Mapped[str] = mapped_column(Text, nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=true(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    owner: Mapped["User"] = relationship(back_populates="links")
    clicks: Mapped[list["Click"]] = relationship(
        back_populates="link",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        # expires_at is always timezone-aware thanks to DateTime(timezone=True).
        return self.expires_at <= datetime.now(timezone.utc)

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<Link code={self.short_code!r} url={self.original_url!r}>"

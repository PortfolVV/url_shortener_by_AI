"""Click event used for the minimal analytics of authenticated users."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.postgre.base_class import Base

if TYPE_CHECKING:  # pragma: no cover
    from src.models.link import Link


class Click(Base):
    __tablename__ = "clicks"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    link_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("links.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    clicked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    referer: Mapped[str | None] = mapped_column(Text, nullable=True)
    referer_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)

    link: Mapped["Link"] = relationship(back_populates="clicks")

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<Click link_id={self.link_id} at={self.clicked_at}>"

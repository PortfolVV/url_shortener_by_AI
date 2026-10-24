"""Declarative base shared by every SQLAlchemy model."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all PostgreSQL models."""

    pass

"""Importing the models here guarantees that they are registered on
``Base.metadata`` before Alembic inspects it (autogenerate / migrations)."""

from src.models.click import Click
from src.models.link import Link
from src.models.user import User

__all__ = ["Click", "Link", "User"]

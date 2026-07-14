"""Shared SQLAlchemy column helpers for ORM models."""

from enum import Enum as PyEnum

from sqlalchemy import Enum


def str_enum(enum_cls: type[PyEnum], *, length: int = 32) -> Enum:
    """Store a Python StrEnum as VARCHAR (avoids brittle Postgres ENUM types)."""
    return Enum(
        enum_cls,
        values_callable=lambda members: [item.value for item in members],
        native_enum=False,
        length=length,
    )

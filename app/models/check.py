import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.package import Program
from app.domain.status import CheckStatus
from app.models._helpers import str_enum

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.issue import Issue


class Check(Base):
    __tablename__ = "checks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    program: Mapped[Program] = mapped_column(
        str_enum(Program), nullable=False, index=True
    )
    status: Mapped[CheckStatus] = mapped_column(
        str_enum(CheckStatus),
        nullable=False,
        index=True,
    )
    status_label: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    extracted: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    documents: Mapped[list["Document"]] = relationship(
        back_populates="check",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    issues: Mapped[list["Issue"]] = relationship(
        back_populates="check",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.issues import IssueLevel
from app.models._helpers import str_enum

if TYPE_CHECKING:
    from app.models.check import Check
    from app.models.document import Document


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    check_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("checks.id", name="fk_issues_check_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "documents.id", name="fk_issues_document_id", ondelete="SET NULL"
        ),
        nullable=True,
        index=True,
    )
    level: Mapped[IssueLevel] = mapped_column(
        str_enum(IssueLevel, length=16),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    check: Mapped["Check"] = relationship(back_populates="issues")
    document: Mapped["Document | None"] = relationship(back_populates="issues")

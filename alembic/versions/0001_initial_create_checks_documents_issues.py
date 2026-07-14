"""create checks, documents, and issues tables

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-14 17:40:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "checks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("program", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("status_label", sa.String(length=255), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("extracted", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "checked_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_checks_created_at"), "checks", ["created_at"], unique=False
    )
    op.create_index(op.f("ix_checks_program"), "checks", ["program"], unique=False)
    op.create_index(op.f("ix_checks_status"), "checks", ["status"], unique=False)

    op.create_table(
        "documents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("check_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("original_name", sa.String(length=512), nullable=False),
        sa.Column("detected_type", sa.String(length=32), nullable=True),
        sa.Column("content_type", sa.String(length=128), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["check_id"],
            ["checks.id"],
            name="fk_documents_check_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_documents_check_id"), "documents", ["check_id"], unique=False
    )

    op.create_table(
        "issues",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("check_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["check_id"],
            ["checks.id"],
            name="fk_issues_check_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name="fk_issues_document_id",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_issues_check_id"), "issues", ["check_id"], unique=False)
    op.create_index(
        op.f("ix_issues_document_id"), "issues", ["document_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_issues_document_id"), table_name="issues")
    op.drop_index(op.f("ix_issues_check_id"), table_name="issues")
    op.drop_table("issues")
    op.drop_index(op.f("ix_documents_check_id"), table_name="documents")
    op.drop_table("documents")
    op.drop_index(op.f("ix_checks_status"), table_name="checks")
    op.drop_index(op.f("ix_checks_program"), table_name="checks")
    op.drop_index(op.f("ix_checks_created_at"), table_name="checks")
    op.drop_table("checks")

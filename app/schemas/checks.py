"""Pydantic request/response models for the checks API."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.document_types import DocumentType
from app.domain.issues import IssueLevel
from app.domain.package import Program
from app.domain.status import CheckStatus


def size_bytes_to_kb(size_bytes: int) -> int:
    """Convert byte size to whole kilobytes (rounded up, minimum 0)."""
    if size_bytes <= 0:
        return 0
    return (size_bytes + 1023) // 1024


class IssueOut(BaseModel):
    level: IssueLevel
    message: str


class DocumentOut(BaseModel):
    name: str
    detected_type: DocumentType | None
    size_kb: int


class CheckDetailOut(BaseModel):
    """Full check result (POST /api/checks and GET /api/checks/{id})."""

    model_config = ConfigDict(from_attributes=True)

    check_id: uuid.UUID
    status: CheckStatus
    status_label: str
    reason: str
    issues: list[IssueOut]
    documents: list[DocumentOut]
    extracted: dict[str, Any] | None = None
    checked_at: datetime


class CheckListItemOut(BaseModel):
    """Summary row for GET /api/checks."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    program: Program
    status: CheckStatus
    documents_count: int = Field(description="Number of uploaded documents")

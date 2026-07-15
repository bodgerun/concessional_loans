"""Map ORM check rows to API response schemas."""

from app.models.check import Check
from app.schemas.checks import (
    CheckDetailOut,
    CheckListItemOut,
    DocumentOut,
    IssueOut,
    size_bytes_to_kb,
)


def check_to_detail(check: Check) -> CheckDetailOut:
    return CheckDetailOut(
        check_id=check.id,
        status=check.status,
        status_label=check.status_label,
        reason=check.reason,
        issues=[
            IssueOut(level=issue.level, message=issue.message) for issue in check.issues
        ],
        documents=[
            DocumentOut(
                name=document.original_name,
                detected_type=document.detected_type,
                size_kb=size_bytes_to_kb(document.size_bytes),
            )
            for document in check.documents
        ],
        extracted=check.extracted,
        checked_at=check.checked_at,
    )


def check_to_list_item(check: Check) -> CheckListItemOut:
    return CheckListItemOut(
        id=check.id,
        created_at=check.created_at,
        program=check.program,
        status=check.status,
        documents_count=len(check.documents),
    )

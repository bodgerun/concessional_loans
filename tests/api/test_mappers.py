"""Tests for check API mappers and schema helpers."""

import uuid
from datetime import UTC, datetime

from app.api.mappers import check_to_detail, check_to_list_item
from app.domain.document_types import DocumentType
from app.domain.issues import IssueLevel
from app.domain.package import Program
from app.domain.status import CheckStatus
from app.models.check import Check
from app.models.document import Document
from app.models.issue import Issue
from app.schemas.checks import size_bytes_to_kb


def test_size_bytes_to_kb_rounds_up() -> None:
    assert size_bytes_to_kb(0) == 0
    assert size_bytes_to_kb(1) == 1
    assert size_bytes_to_kb(1024) == 1
    assert size_bytes_to_kb(1025) == 2


def _sample_check(*, with_error: bool = False) -> Check:
    check_id = uuid.uuid4()
    now = datetime.now(UTC)
    check = Check(
        id=check_id,
        program=Program.FEDERAL,
        status=CheckStatus.REJECTED if with_error else CheckStatus.APPROVED,
        status_label=(
            "Нельзя заявлять в банк" if with_error else "Можно заявлять в банк"
        ),
        reason=(
            "Отсутствует обязательный документ: спецификация."
            if with_error
            else "Пакет документов соответствует требованиям программы."
        ),
        extracted=None,
        created_at=now,
        checked_at=now,
    )
    document = Document(
        id=uuid.uuid4(),
        check_id=check_id,
        original_name="договор_47.pdf",
        detected_type=DocumentType.CONTRACT,
        content_type="application/pdf",
        size_bytes=142 * 1024,
        storage_path=f"{check_id}/договор_47.pdf",
        created_at=now,
    )
    check.documents.append(document)
    if with_error:
        check.issues.append(
            Issue(
                id=uuid.uuid4(),
                check_id=check_id,
                document_id=None,
                level=IssueLevel.ERROR,
                message="Отсутствует обязательный документ: спецификация",
                created_at=now,
            )
        )
    return check


def test_check_to_detail_matches_assignment_shape() -> None:
    check = _sample_check(with_error=True)

    detail = check_to_detail(check)

    assert detail.check_id == check.id
    assert detail.status == CheckStatus.REJECTED
    assert detail.status_label == "Нельзя заявлять в банк"
    assert detail.documents[0].name == "договор_47.pdf"
    assert detail.documents[0].detected_type == DocumentType.CONTRACT
    assert detail.documents[0].size_kb == 142
    assert detail.issues[0].level == IssueLevel.ERROR
    assert detail.extracted is None


def test_check_to_list_item_includes_document_count() -> None:
    check = _sample_check()

    item = check_to_list_item(check)

    assert item.id == check.id
    assert item.program == Program.FEDERAL
    assert item.status == CheckStatus.APPROVED
    assert item.documents_count == 1

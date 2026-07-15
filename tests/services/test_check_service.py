"""Tests for CheckService orchestration (storage + domain + persistence)."""

import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.domain.package import Program
from app.domain.status import CheckStatus
from app.models.check import Check
from app.services.check_service import CheckService, IncomingFile
from app.services.storage import LocalFileStorage


@pytest.fixture
def storage(tmp_path: Path) -> LocalFileStorage:
    return LocalFileStorage(tmp_path / "uploads")


def _mock_db_for_create(captured: list[Check]) -> MagicMock:
    """Session mock that records the added Check and returns it from get_check."""
    db = MagicMock()

    def add(obj: object) -> None:
        if isinstance(obj, Check):
            captured.append(obj)

    db.add.side_effect = add

    def scalars(statement: object) -> MagicMock:
        result = MagicMock()
        result.first.return_value = captured[-1] if captured else None
        return result

    db.scalars.side_effect = scalars
    return db


def test_create_check_stores_files_and_persists_rejected_package(
    storage: LocalFileStorage,
) -> None:
    captured: list[Check] = []
    db = _mock_db_for_create(captured)
    service = CheckService(db, storage)

    result = service.create_check(
        Program.FEDERAL,
        [
            IncomingFile("договор.pdf", b"%PDF-contract", "application/pdf"),
            IncomingFile("счёт.pdf", b"%PDF-invoice", "application/pdf"),
        ],
    )

    assert result.status == CheckStatus.REJECTED
    assert result.program == Program.FEDERAL
    assert len(result.documents) == 2
    assert any(
        issue.message.startswith("Отсутствует обязательный документ")
        for issue in result.issues
    )
    assert storage.check_dir(result.id).is_dir()
    assert (storage.check_dir(result.id) / "договор.pdf").is_file()
    db.commit.assert_called_once()
    db.rollback.assert_not_called()


def test_create_check_approves_complete_regional_package(
    storage: LocalFileStorage,
) -> None:
    captured: list[Check] = []
    db = _mock_db_for_create(captured)
    service = CheckService(db, storage)

    result = service.create_check(
        Program.REGIONAL,
        [
            IncomingFile("договор.pdf", b"a" * 100, "application/pdf"),
            IncomingFile("счёт.pdf", b"b" * 100, "application/pdf"),
            IncomingFile("акт.pdf", b"c" * 100, "application/pdf"),
        ],
    )

    assert result.status == CheckStatus.APPROVED
    assert result.issues == []
    assert {doc.detected_type.value for doc in result.documents} == {
        "contract",
        "invoice",
        "act",
    }


def test_create_check_links_file_level_issue_to_document(
    storage: LocalFileStorage,
) -> None:
    captured: list[Check] = []
    db = _mock_db_for_create(captured)
    service = CheckService(db, storage)

    result = service.create_check(
        Program.REGIONAL,
        [
            IncomingFile("договор.pdf", b"a", "application/pdf"),
            IncomingFile("счёт.pdf", b"b", "application/pdf"),
            IncomingFile("акт.pdf", b"c", "application/pdf"),
            IncomingFile("scan_0041.jpg", b"d", "image/jpeg"),
        ],
    )

    warning = next(issue for issue in result.issues if issue.level.value == "warning")
    assert "scan_0041.jpg" in warning.message
    assert warning.document_id is not None
    linked = next(doc for doc in result.documents if doc.id == warning.document_id)
    assert linked.original_name == "scan_0041.jpg"


def test_create_check_rolls_back_and_deletes_files_on_db_failure(
    storage: LocalFileStorage,
) -> None:
    db = MagicMock()
    db.commit.side_effect = RuntimeError("db down")
    service = CheckService(db, storage)

    with pytest.raises(RuntimeError, match="db down"):
        service.create_check(
            Program.REGIONAL,
            [IncomingFile("договор.pdf", b"data", "application/pdf")],
        )

    db.rollback.assert_called_once()
    # check_id is unknown here; ensure upload root has no leftover check dirs.
    assert list(storage.root.iterdir()) == []


def test_get_check_returns_none_when_missing(storage: LocalFileStorage) -> None:
    db = MagicMock()
    result = MagicMock()
    result.first.return_value = None
    db.scalars.return_value = result
    service = CheckService(db, storage)

    assert service.get_check(uuid.uuid4()) is None


def test_list_checks_returns_scalars_list(storage: LocalFileStorage) -> None:
    db = MagicMock()
    check = MagicMock(spec=Check)
    db.scalars.return_value = [check]
    service = CheckService(db, storage)

    assert service.list_checks() == [check]

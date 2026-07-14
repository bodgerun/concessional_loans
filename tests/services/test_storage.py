"""Tests for local file storage."""

import uuid
from pathlib import Path

import pytest

from app.services.storage import LocalFileStorage


@pytest.fixture
def storage(tmp_path: Path) -> LocalFileStorage:
    return LocalFileStorage(tmp_path / "uploads")


def test_save_bytes_creates_check_directory_and_file(storage: LocalFileStorage) -> None:
    check_id = uuid.uuid4()
    payload = b"%PDF-1.4 fake"

    stored = storage.save_bytes(check_id, "договор_47.pdf", payload)

    assert stored.original_name == "договор_47.pdf"
    assert stored.stored_name == "договор_47.pdf"
    assert stored.storage_path == f"{check_id}/договор_47.pdf"
    assert stored.size_bytes == len(payload)
    assert stored.absolute_path.is_file()
    assert stored.absolute_path.read_bytes() == payload
    assert storage.check_dir(check_id).is_dir()


def test_save_bytes_strips_path_traversal_from_filename(
    storage: LocalFileStorage,
) -> None:
    check_id = uuid.uuid4()

    stored = storage.save_bytes(check_id, "../../etc/passwd.pdf", b"data")

    assert stored.stored_name == "passwd.pdf"
    assert stored.storage_path == f"{check_id}/passwd.pdf"
    assert stored.absolute_path.parent == storage.check_dir(check_id)
    # Nothing written outside the upload root.
    assert not (storage.root.parent / "etc").exists()


def test_save_bytes_deduplicates_same_filename(storage: LocalFileStorage) -> None:
    check_id = uuid.uuid4()

    first = storage.save_bytes(check_id, "акт.pdf", b"one")
    second = storage.save_bytes(check_id, "акт.pdf", b"two")

    assert first.stored_name == "акт.pdf"
    assert second.stored_name == "акт_1.pdf"
    assert first.absolute_path.read_bytes() == b"one"
    assert second.absolute_path.read_bytes() == b"two"


def test_resolve_returns_absolute_path_under_root(storage: LocalFileStorage) -> None:
    check_id = uuid.uuid4()
    stored = storage.save_bytes(check_id, "счёт.pdf", b"x")

    resolved = storage.resolve(stored.storage_path)

    assert resolved == stored.absolute_path


def test_resolve_rejects_path_traversal(storage: LocalFileStorage) -> None:
    storage.ensure_root()

    with pytest.raises(ValueError, match="escapes upload root"):
        storage.resolve("../outside.txt")


def test_delete_check_removes_directory(storage: LocalFileStorage) -> None:
    check_id = uuid.uuid4()
    storage.save_bytes(check_id, "договор.pdf", b"data")
    assert storage.check_dir(check_id).exists()

    storage.delete_check(check_id)

    assert not storage.check_dir(check_id).exists()


def test_safe_filename_fallback_for_blank_name(storage: LocalFileStorage) -> None:
    check_id = uuid.uuid4()

    stored = storage.save_bytes(check_id, "   ", b"x")

    assert stored.stored_name == "unnamed"
    assert stored.absolute_path.is_file()

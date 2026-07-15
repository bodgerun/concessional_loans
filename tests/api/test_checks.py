"""HTTP-level tests for /api/checks (service dependency overridden)."""

import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_check_service
from app.domain.document_types import DocumentType
from app.domain.issues import IssueLevel
from app.domain.package import Program
from app.domain.status import CheckStatus
from app.main import app
from app.models.check import Check
from app.models.document import Document
from app.models.issue import Issue


def _check(*, check_id: uuid.UUID | None = None) -> Check:
    check_id = check_id or uuid.uuid4()
    now = datetime.now(UTC)
    check = Check(
        id=check_id,
        program=Program.FEDERAL,
        status=CheckStatus.REJECTED,
        status_label="Нельзя заявлять в банк",
        reason="Отсутствует обязательный документ: спецификация.",
        extracted=None,
        created_at=now,
        checked_at=now,
    )
    check.documents.append(
        Document(
            id=uuid.uuid4(),
            check_id=check_id,
            original_name="договор.pdf",
            detected_type=DocumentType.CONTRACT,
            content_type="application/pdf",
            size_bytes=2048,
            storage_path=f"{check_id}/договор.pdf",
            created_at=now,
        )
    )
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


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def mock_service() -> object:
    from unittest.mock import MagicMock

    service = MagicMock()
    app.dependency_overrides[get_check_service] = lambda: service
    yield service
    app.dependency_overrides.clear()


def test_post_checks_returns_201(client: TestClient, mock_service: object) -> None:
    created = _check()
    mock_service.create_check.return_value = created

    response = client.post(
        "/api/checks",
        data={"program": "federal"},
        files=[("files", ("договор.pdf", b"%PDF", "application/pdf"))],
    )

    assert response.status_code == 201
    body = response.json()
    assert body["check_id"] == str(created.id)
    assert body["status"] == "rejected"
    assert body["documents"][0]["name"] == "договор.pdf"
    assert body["documents"][0]["size_kb"] == 2
    mock_service.create_check.assert_called_once()


def test_post_checks_rejects_invalid_program(
    client: TestClient, mock_service: object
) -> None:
    response = client.post(
        "/api/checks",
        data={"program": "unknown"},
        files=[("files", ("договор.pdf", b"x", "application/pdf"))],
    )

    assert response.status_code == 422
    mock_service.create_check.assert_not_called()


def test_post_checks_missing_files_returns_400(
    client: TestClient, mock_service: object
) -> None:
    response = client.post("/api/checks", data={"program": "federal"})

    assert response.status_code == 400
    assert response.json()["detail"] == "At least one file is required"
    mock_service.create_check.assert_not_called()


def test_post_checks_missing_program_returns_422(
    client: TestClient, mock_service: object
) -> None:
    response = client.post(
        "/api/checks",
        files=[("files", ("договор.pdf", b"x", "application/pdf"))],
    )

    assert response.status_code == 422
    mock_service.create_check.assert_not_called()


def test_get_checks_returns_list(client: TestClient, mock_service: object) -> None:
    mock_service.list_checks.return_value = [_check()]

    response = client.get("/api/checks")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["documents_count"] == 1
    assert body[0]["program"] == "federal"


def test_get_check_by_id_returns_detail(
    client: TestClient, mock_service: object
) -> None:
    created = _check()
    mock_service.get_check.return_value = created

    response = client.get(f"/api/checks/{created.id}")

    assert response.status_code == 200
    assert response.json()["check_id"] == str(created.id)


def test_get_check_by_id_returns_404(client: TestClient, mock_service: object) -> None:
    mock_service.get_check.return_value = None
    missing = uuid.uuid4()

    response = client.get(f"/api/checks/{missing}")

    assert response.status_code == 404
    assert str(missing) in response.json()["detail"]


def test_get_check_by_id_invalid_uuid_returns_422(
    client: TestClient, mock_service: object
) -> None:
    response = client.get("/api/checks/not-a-uuid")

    assert response.status_code == 422
    mock_service.get_check.assert_not_called()

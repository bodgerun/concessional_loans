"""Package validation: format, size, type recognition, and completeness."""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from app.domain.document_types import (
    DOCUMENT_TYPE_LABELS,
    DocumentType,
    detect_document_type,
)
from app.domain.issues import Issue, IssueLevel
from app.domain.status import CheckOutcome, resolve_status


class Program(StrEnum):
    FEDERAL = "federal"
    REGIONAL = "regional"


_ALLOWED_EXTENSIONS: frozenset[str] = frozenset(
    {".pdf", ".docx", ".jpg", ".jpeg", ".png"}
)
_MAX_FILE_SIZE_BYTES: int = 20 * 1024 * 1024  # 20 MB
_MAX_FILE_SIZE_MB: int = _MAX_FILE_SIZE_BYTES // (1024 * 1024)

_REQUIRED_DOCUMENTS: dict[Program, frozenset[DocumentType]] = {
    Program.FEDERAL: frozenset(
        {
            DocumentType.CONTRACT,
            DocumentType.SPECIFICATION,
            DocumentType.INVOICE,
            DocumentType.ACT,
        }
    ),
    Program.REGIONAL: frozenset(
        {
            DocumentType.CONTRACT,
            DocumentType.INVOICE,
            DocumentType.ACT,
        }
    ),
}


@dataclass(frozen=True)
class UploadedFile:
    name: str
    size_bytes: int


@dataclass(frozen=True)
class DocumentInfo:
    name: str
    detected_type: DocumentType | None
    size_bytes: int


@dataclass(frozen=True)
class PackageCheckResult:
    documents: list[DocumentInfo]
    issues: list[Issue]
    outcome: CheckOutcome


def evaluate_package(program: Program, files: list[UploadedFile]) -> PackageCheckResult:
    """Run all synchronous package checks and resolve the final status."""
    documents: list[DocumentInfo] = []
    issues: list[Issue] = []
    detected_types: set[DocumentType] = set()

    for uploaded in files:
        detected_type = detect_document_type(uploaded.name)

        documents.append(
            DocumentInfo(
                name=uploaded.name,
                detected_type=detected_type,
                size_bytes=uploaded.size_bytes,
            )
        )

        extension_issue = _validate_extension(uploaded.name)
        if extension_issue is not None:
            issues.append(extension_issue)

        size_issue = _validate_size(uploaded.name, uploaded.size_bytes)
        if size_issue is not None:
            issues.append(size_issue)

        file_is_valid = extension_issue is None and size_issue is None

        if detected_type is None:
            issues.append(
                Issue(
                    level=IssueLevel.WARNING,
                    message=f"Не удалось определить тип документа: «{uploaded.name}»",
                )
            )
        elif file_is_valid:
            # Invalid files must not satisfy completeness (e.g. договор.exe).
            detected_types.add(detected_type)

    issues.extend(_check_completeness(program, detected_types))

    return PackageCheckResult(
        documents=documents,
        issues=issues,
        outcome=resolve_status(issues),
    )


def _validate_extension(filename: str) -> Issue | None:
    extension = _extension_of(filename)
    if extension not in _ALLOWED_EXTENSIONS:
        return Issue(
            level=IssueLevel.ERROR,
            message=f"Недопустимый формат файла: «{filename}»",
        )
    return None


def _validate_size(filename: str, size_bytes: int) -> Issue | None:
    if size_bytes > _MAX_FILE_SIZE_BYTES:
        return Issue(
            level=IssueLevel.ERROR,
            message=(f"Размер файла превышает {_MAX_FILE_SIZE_MB} МБ: «{filename}»"),
        )
    return None


def _check_completeness(
    program: Program,
    detected_types: set[DocumentType],
) -> list[Issue]:
    required = _REQUIRED_DOCUMENTS[program]
    missing = sorted(required - detected_types, key=lambda item: item.value)
    return [
        Issue(
            level=IssueLevel.ERROR,
            message=(
                f"Отсутствует обязательный документ: {DOCUMENT_TYPE_LABELS[doc_type]}"
            ),
        )
        for doc_type in missing
    ]


def _extension_of(filename: str) -> str:
    return Path(filename).suffix.lower()

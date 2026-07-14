"""Tests for package validation: format, size, completeness, and status."""

import pytest

from app.domain.document_types import DocumentType
from app.domain.issues import IssueLevel
from app.domain.package import PackageCheckResult, Program, evaluate_package
from app.domain.status import CheckStatus
from tests.helpers import OVERSIZED_BYTES, uploaded


def _messages(result: PackageCheckResult) -> list[str]:
    return [issue.message for issue in result.issues]


def _error_messages(result: PackageCheckResult) -> list[str]:
    return [
        issue.message
        for issue in result.issues
        if issue.level == IssueLevel.ERROR
    ]


def _warning_messages(result: PackageCheckResult) -> list[str]:
    return [
        issue.message
        for issue in result.issues
        if issue.level == IssueLevel.WARNING
    ]


FEDERAL_COMPLETE = [
    uploaded("договор.pdf"),
    uploaded("спецификация.pdf"),
    uploaded("счёт.pdf"),
    uploaded("акт.pdf"),
]

REGIONAL_COMPLETE = [
    uploaded("contract.pdf"),
    uploaded("invoice.pdf"),
    uploaded("act.pdf"),
]


def test_federal_complete_package_is_approved() -> None:
    result = evaluate_package(Program.FEDERAL, FEDERAL_COMPLETE)

    assert result.outcome.status == CheckStatus.APPROVED
    assert result.issues == []
    assert [doc.detected_type for doc in result.documents] == [
        DocumentType.CONTRACT,
        DocumentType.SPECIFICATION,
        DocumentType.INVOICE,
        DocumentType.ACT,
    ]


def test_regional_complete_package_without_specification_is_approved() -> None:
    result = evaluate_package(Program.REGIONAL, REGIONAL_COMPLETE)

    assert result.outcome.status == CheckStatus.APPROVED
    assert result.issues == []


def test_federal_requires_specification() -> None:
    files = [
        uploaded("договор.pdf"),
        uploaded("счёт.pdf"),
        uploaded("акт.pdf"),
    ]
    result = evaluate_package(Program.FEDERAL, files)

    assert result.outcome.status == CheckStatus.REJECTED
    assert "Отсутствует обязательный документ: спецификация" in _error_messages(result)


def test_regional_does_not_require_specification() -> None:
    files = [
        uploaded("договор.pdf"),
        uploaded("счёт.pdf"),
        uploaded("акт.pdf"),
    ]
    result = evaluate_package(Program.REGIONAL, files)

    assert result.outcome.status == CheckStatus.APPROVED
    assert _error_messages(result) == []


def test_empty_package_reports_all_required_documents() -> None:
    result = evaluate_package(Program.FEDERAL, [])

    assert result.outcome.status == CheckStatus.REJECTED
    assert _error_messages(result) == [
        "Отсутствует обязательный документ: акт",
        "Отсутствует обязательный документ: договор",
        "Отсутствует обязательный документ: счёт",
        "Отсутствует обязательный документ: спецификация",
    ]


@pytest.mark.parametrize(
    "filename",
    ["notes.txt", "archive.zip", "slide.pptx", "data.xlsx", "script.exe"],
)
def test_disallowed_extension_is_error(filename: str) -> None:
    result = evaluate_package(Program.REGIONAL, [uploaded(filename)])

    assert f"Недопустимый формат файла: «{filename}»" in _error_messages(result)
    assert result.outcome.status == CheckStatus.REJECTED


@pytest.mark.parametrize(
    "filename",
    ["договор.PDF", "счёт.DOCX", "акт.JPG", "упд.JPEG", "invoice.PNG"],
)
def test_allowed_extensions_case_insensitive(filename: str) -> None:
    # Completeness will still fail; we only assert format is accepted.
    result = evaluate_package(Program.REGIONAL, [uploaded(filename)])

    assert not any("Недопустимый формат файла" in msg for msg in _messages(result))


def test_oversized_file_is_error() -> None:
    result = evaluate_package(
        Program.REGIONAL,
        [uploaded("договор.pdf", size_bytes=OVERSIZED_BYTES)],
    )

    assert "Размер файла превышает 20 МБ: «договор.pdf»" in _error_messages(result)
    assert result.outcome.status == CheckStatus.REJECTED


def test_file_at_exactly_max_size_is_allowed() -> None:
    max_bytes = 20 * 1024 * 1024
    result = evaluate_package(
        Program.REGIONAL,
        [
            uploaded("договор.pdf", size_bytes=max_bytes),
            uploaded("счёт.pdf"),
            uploaded("акт.pdf"),
        ],
    )

    assert not any("Размер файла превышает" in msg for msg in _messages(result))
    assert result.outcome.status == CheckStatus.APPROVED


def test_unrecognized_filename_is_warning() -> None:
    result = evaluate_package(
        Program.REGIONAL,
        [
            *REGIONAL_COMPLETE,
            uploaded("scan_0041.jpg"),
        ],
    )

    assert result.outcome.status == CheckStatus.APPROVED
    assert "Не удалось определить тип документа: «scan_0041.jpg»" in _warning_messages(
        result
    )


def test_invalid_file_does_not_satisfy_completeness() -> None:
    # Recognizable name but disallowed extension — must not count as contract.
    result = evaluate_package(
        Program.REGIONAL,
        [
            uploaded("договор.exe"),
            uploaded("счёт.pdf"),
            uploaded("акт.pdf"),
        ],
    )

    assert result.outcome.status == CheckStatus.REJECTED
    assert "Отсутствует обязательный документ: договор" in _error_messages(result)
    assert "Недопустимый формат файла: «договор.exe»" in _error_messages(result)


def test_oversized_recognized_file_does_not_satisfy_completeness() -> None:
    result = evaluate_package(
        Program.REGIONAL,
        [
            uploaded("договор.pdf", size_bytes=OVERSIZED_BYTES),
            uploaded("счёт.pdf"),
            uploaded("акт.pdf"),
        ],
    )

    assert "Отсутствует обязательный документ: договор" in _error_messages(result)


def test_documents_preserve_order_and_sizes() -> None:
    files = [
        uploaded("договор.pdf", size_bytes=2048),
        uploaded("unknown.bin", size_bytes=512),
    ]
    result = evaluate_package(Program.FEDERAL, files)

    assert len(result.documents) == 2
    assert result.documents[0].name == "договор.pdf"
    assert result.documents[0].detected_type == DocumentType.CONTRACT
    assert result.documents[0].size_bytes == 2048
    assert result.documents[1].name == "unknown.bin"
    assert result.documents[1].detected_type is None
    assert result.documents[1].size_bytes == 512


def test_duplicate_types_still_satisfy_completeness() -> None:
    files = [
        uploaded("договор_1.pdf"),
        uploaded("договор_2.pdf"),
        uploaded("счёт.pdf"),
        uploaded("акт.pdf"),
    ]
    result = evaluate_package(Program.REGIONAL, files)

    assert result.outcome.status == CheckStatus.APPROVED


def test_combined_issues_produce_rejected_with_primary_reason() -> None:
    result = evaluate_package(
        Program.FEDERAL,
        [
            uploaded("договор.pdf"),
            uploaded("notes.txt"),
            uploaded("scan.jpg"),
            uploaded("счёт.pdf", size_bytes=OVERSIZED_BYTES),
        ],
    )

    assert result.outcome.status == CheckStatus.REJECTED
    assert result.outcome.status_label == "Нельзя заявлять в банк"
    # First error in traversal order becomes the reason (notes.txt format).
    assert result.outcome.reason == "Недопустимый формат файла: «notes.txt»."

    errors = _error_messages(result)
    warnings = _warning_messages(result)
    assert "Недопустимый формат файла: «notes.txt»" in errors
    assert "Размер файла превышает 20 МБ: «счёт.pdf»" in errors
    assert "Отсутствует обязательный документ: спецификация" in errors
    assert "Отсутствует обязательный документ: акт" in errors
    assert "Не удалось определить тип документа: «scan.jpg»" in warnings
    # Oversized invoice must not count toward completeness.
    assert "Отсутствует обязательный документ: счёт" in errors

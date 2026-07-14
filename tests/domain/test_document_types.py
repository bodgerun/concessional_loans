"""Tests for filename-based document type detection."""

import pytest

from app.domain.document_types import DocumentType, detect_document_type


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("договор_47.pdf", DocumentType.CONTRACT),
        ("Договор поставки.docx", DocumentType.CONTRACT),
        ("contract_2024.pdf", DocumentType.CONTRACT),
        ("CONTRACT.PDF", DocumentType.CONTRACT),
        ("спецификация_к_договору.pdf", DocumentType.SPECIFICATION),
        ("specification.xlsx", DocumentType.SPECIFICATION),
        ("spec_01.pdf", DocumentType.SPECIFICATION),
        ("счёт_на_оплату.pdf", DocumentType.INVOICE),
        ("счет_12.jpg", DocumentType.INVOICE),
        ("invoice_final.png", DocumentType.INVOICE),
        ("акт_выполненных_работ.pdf", DocumentType.ACT),
        ("упд_003.pdf", DocumentType.ACT),
        ("UPD_scan.jpg", DocumentType.ACT),
        ("act_signed.docx", DocumentType.ACT),
    ],
)
def test_detects_known_patterns(filename: str, expected: DocumentType) -> None:
    assert detect_document_type(filename) == expected


@pytest.mark.parametrize(
    "filename",
    [
        "scan_0041.jpg",
        "document.pdf",
        "файл.docx",
        "random_name.png",
        "",
    ],
)
def test_returns_none_for_unrecognized_names(filename: str) -> None:
    assert detect_document_type(filename) is None


def test_uses_stem_ignoring_path_and_extension() -> None:
    assert detect_document_type("uploads/batch_1/договор_47.pdf") == DocumentType.CONTRACT
    assert detect_document_type("invoice") == DocumentType.INVOICE


def test_normalizes_yo_to_ye() -> None:
    # "счёт" pattern is stored with "ё"; filenames may use either letter.
    assert detect_document_type("счёт.pdf") == DocumentType.INVOICE
    assert detect_document_type("счет.pdf") == DocumentType.INVOICE


def test_specification_wins_over_overlapping_tokens() -> None:
    # "спецификация" is checked before "договор"; both tokens present.
    assert detect_document_type("спецификация_договор.pdf") == DocumentType.SPECIFICATION


def test_does_not_match_token_inside_another_word() -> None:
    # "act" must not match as a substring of "contract" (token boundaries).
    assert detect_document_type("contract.pdf") == DocumentType.CONTRACT
    # "spec" must not match inside an unrelated longer stem without separators.
    assert detect_document_type("inspector.pdf") is None

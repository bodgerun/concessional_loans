"""Filename-based document type detection."""

import re
from enum import StrEnum
from pathlib import Path


class DocumentType(StrEnum):
    CONTRACT = "contract"
    SPECIFICATION = "specification"
    INVOICE = "invoice"
    ACT = "act"


# Human-readable labels used in issue/reason messages (Russian).
DOCUMENT_TYPE_LABELS: dict[DocumentType, str] = {
    DocumentType.CONTRACT: "договор",
    DocumentType.SPECIFICATION: "спецификация",
    DocumentType.INVOICE: "счёт",
    DocumentType.ACT: "акт",
}

_TOKEN_CHARS = r"0-9a-zа-я"

# Longer / more specific patterns first so "spec" wins over shorter overlaps.
_TYPE_PATTERNS: tuple[tuple[DocumentType, tuple[str, ...]], ...] = (
    (
        DocumentType.SPECIFICATION,
        ("спецификация", "specification", "spec"),
    ),
    (
        DocumentType.CONTRACT,
        ("договор", "contract"),
    ),
    (
        DocumentType.INVOICE,
        ("счёт", "счет", "invoice"),
    ),
    (
        DocumentType.ACT,
        ("упд", "upd", "акт", "act"),
    ),
)


def detect_document_type(filename: str) -> DocumentType | None:
    """
    Detect document type from the original filename.

    Supports Russian and English name variants from the assignment brief.
    Returns None when the type cannot be determined.
    """
    stem = _normalize_text(Path(filename).stem)
    for document_type, patterns in _TYPE_PATTERNS:
        if any(_has_token(stem, _normalize_text(pattern)) for pattern in patterns):
            return document_type
    return None


def _normalize_text(value: str) -> str:
    return value.lower().replace("ё", "е")


def _has_token(stem: str, token: str) -> bool:
    """
    Return True if `token` appears in `stem` as a whole word,
    not as part of another word.
    """
    return re.search(
        rf"(?<![{_TOKEN_CHARS}]){re.escape(token)}(?![{_TOKEN_CHARS}])",
        stem,
    ) is not None

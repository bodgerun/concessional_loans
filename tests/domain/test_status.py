"""Tests for final check status and reason generation."""

from app.domain.issues import Issue, IssueLevel
from app.domain.status import (
    CheckStatus,
    in_progress_outcome,
    resolve_status,
)


def test_no_issues_is_approved() -> None:
    outcome = resolve_status([])

    assert outcome.status == CheckStatus.APPROVED
    assert outcome.status_label == "Можно заявлять в банк"
    assert outcome.reason == "Пакет документов соответствует требованиям программы."


def test_warnings_alone_do_not_block_approval() -> None:
    outcome = resolve_status(
        [
            Issue(
                level=IssueLevel.WARNING,
                message="Не удалось определить тип документа: «scan.jpg»",
            )
        ]
    )

    assert outcome.status == CheckStatus.APPROVED
    assert outcome.status_label == "Можно заявлять в банк"


def test_any_error_yields_rejected() -> None:
    outcome = resolve_status(
        [
            Issue(
                level=IssueLevel.WARNING,
                message="Не удалось определить тип документа: «scan.jpg»",
            ),
            Issue(
                level=IssueLevel.ERROR,
                message="Отсутствует обязательный документ: спецификация",
            ),
        ]
    )

    assert outcome.status == CheckStatus.REJECTED
    assert outcome.status_label == "Нельзя заявлять в банк"


def test_rejected_reason_uses_first_error_and_adds_period() -> None:
    outcome = resolve_status(
        [
            Issue(level=IssueLevel.WARNING, message="warning without period"),
            Issue(
                level=IssueLevel.ERROR,
                message="Отсутствует обязательный документ: спецификация",
            ),
            Issue(
                level=IssueLevel.ERROR,
                message="Отсутствует обязательный документ: счёт",
            ),
        ]
    )

    assert outcome.reason == "Отсутствует обязательный документ: спецификация."


def test_rejected_reason_keeps_existing_trailing_period() -> None:
    outcome = resolve_status(
        [
            Issue(
                level=IssueLevel.ERROR,
                message="Недопустимый формат файла: «file.exe».",
            )
        ]
    )

    assert outcome.reason == "Недопустимый формат файла: «file.exe»."


def test_in_progress_outcome() -> None:
    outcome = in_progress_outcome()

    assert outcome.status == CheckStatus.CHECK_IN_PROGRESS
    assert outcome.status_label == "Требуется ручная проверка"
    assert outcome.reason == "Требуется ручная проверка результата."

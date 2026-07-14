"""Final check status and human-readable reason generation."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from app.domain.issues import IssueLevel


class CheckStatus(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    CHECK_IN_PROGRESS = "check_in_progress"


_STATUS_LABELS: dict[CheckStatus, str] = {
    CheckStatus.APPROVED: "Можно заявлять в банк",
    CheckStatus.REJECTED: "Нельзя заявлять в банк",
    CheckStatus.CHECK_IN_PROGRESS: "Требуется ручная проверка",
}


class _IssueLike(Protocol):
    level: IssueLevel
    message: str


@dataclass(frozen=True)
class CheckOutcome:
    status: CheckStatus
    status_label: str
    reason: str


def resolve_status(issues: list[_IssueLike]) -> CheckOutcome:
    """Map collected issues to the final check status.

    Rules (assignment):
    - rejected — at least one error;
    - approved — no errors (warnings alone do not block approval);
    - check_in_progress — reserved for a future async flow (not used yet).
    """
    if any(_is_error(issue) for issue in issues):
        status = CheckStatus.REJECTED
        reason = _reason_for_rejected(issues)
    else:
        status = CheckStatus.APPROVED
        reason = _reason_for_approved()

    return CheckOutcome(
        status=status,
        status_label=_STATUS_LABELS[status],
        reason=reason,
    )


def in_progress_outcome() -> CheckOutcome:
    """Placeholder for a future async check flow."""
    status = CheckStatus.CHECK_IN_PROGRESS
    return CheckOutcome(
        status=status,
        status_label=_STATUS_LABELS[status],
        reason=_reason_for_in_progress(),
    )


def _is_error(issue: _IssueLike) -> bool:
    return issue.level == IssueLevel.ERROR


def _reason_for_approved() -> str:
    return "Пакет документов соответствует требованиям программы."


def _reason_for_in_progress() -> str:
    return "Требуется ручная проверка результата."


def _reason_for_rejected(issues: list[_IssueLike]) -> str:
    errors = [issue for issue in issues if _is_error(issue)]
    if not errors:
        return "Обнаружены нарушения в пакете документов."

    first = errors[0].message
    if not first.endswith("."):
        first = f"{first}."
    return first

"""Issue level and issue records shared across domain modules."""

from dataclasses import dataclass
from enum import StrEnum


class IssueLevel(StrEnum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class Issue:
    level: IssueLevel
    message: str

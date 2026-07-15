"""Orchestrate package validation, file storage, and DB persistence."""

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.package import Program, UploadedFile, evaluate_package
from app.models.check import Check
from app.models.document import Document
from app.models.issue import Issue as IssueRow
from app.services.storage import LocalFileStorage


@dataclass(frozen=True)
class IncomingFile:
    """One uploaded file already read into memory."""

    filename: str
    content: bytes
    content_type: str | None = None


class CheckService:
    """Coordinates domain checks, local storage, and PostgreSQL writes."""

    def __init__(self, db: Session, storage: LocalFileStorage) -> None:
        self._db = db
        self._storage = storage

    def create_check(self, program: Program, files: list[IncomingFile]) -> Check:
        """
        Validate a document package, store files, and persist the result.

        On persistence failure, uploaded files for this check are removed.
        """
        check_id = uuid.uuid4()
        try:
            stored = [
                self._storage.save_bytes(check_id, item.filename, item.content)
                for item in files
            ]

            package = evaluate_package(
                program,
                [
                    UploadedFile(name=item.filename, size_bytes=len(item.content))
                    for item in files
                ],
            )

            check = Check(
                id=check_id,
                program=program,
                status=package.outcome.status,
                status_label=package.outcome.status_label,
                reason=package.outcome.reason,
                extracted=None,
            )

            documents_by_name: dict[str, Document] = {}
            for item, stored_file, doc_info in zip(
                files, stored, package.documents, strict=True
            ):
                document = Document(
                    id=uuid.uuid4(),
                    check_id=check_id,
                    original_name=doc_info.name,
                    detected_type=doc_info.detected_type,
                    content_type=item.content_type,
                    size_bytes=stored_file.size_bytes,
                    storage_path=stored_file.storage_path,
                )
                check.documents.append(document)
                documents_by_name[doc_info.name] = document

            for domain_issue in package.issues:
                check.issues.append(
                    IssueRow(
                        id=uuid.uuid4(),
                        check_id=check_id,
                        document_id=_match_document_id(
                            domain_issue.message, documents_by_name
                        ),
                        level=domain_issue.level,
                        message=domain_issue.message,
                    )
                )

            self._db.add(check)
            self._db.commit()
        except Exception:
            self._db.rollback()
            self._storage.delete_check(check_id)
            raise

        # Re-load with relationships (expire_on_commit clears in-memory collections).
        loaded = self.get_check(check_id)
        if loaded is None:
            raise RuntimeError(
                f"Check {check_id} was committed but could not be reloaded"
            )
        return loaded

    def list_checks(self) -> list[Check]:
        """Return all checks, newest first, with documents loaded for counts."""
        statement = (
            select(Check)
            .options(selectinload(Check.documents))
            .order_by(Check.created_at.desc())
        )
        return list(self._db.scalars(statement))

    def get_check(self, check_id: uuid.UUID) -> Check | None:
        """Return one check with documents and issues, or None if missing."""
        statement = (
            select(Check)
            .where(Check.id == check_id)
            .options(
                selectinload(Check.documents),
                selectinload(Check.issues),
            )
        )
        return self._db.scalars(statement).first()


def _match_document_id(
    message: str,
    documents_by_name: dict[str, Document],
) -> uuid.UUID | None:
    """Link a file-level issue to a document when the filename is in the message."""
    for name, document in documents_by_name.items():
        if name in message:
            return document.id
    return None

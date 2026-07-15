"""HTTP error helpers for consistent status codes and messages."""

from fastapi import HTTPException, status


def bad_request(detail: str) -> HTTPException:
    """400 — request is well-formed enough to parse, but semantically invalid."""
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def not_found(detail: str) -> HTTPException:
    """404 — the requested resource does not exist."""
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

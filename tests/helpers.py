"""Shared helpers for domain tests."""

from app.domain.package import UploadedFile

# 1 KB — well under the 20 MB limit.
SMALL_FILE_BYTES = 1024
# Just over 20 MB.
OVERSIZED_BYTES = 20 * 1024 * 1024 + 1


def uploaded(name: str, size_bytes: int = SMALL_FILE_BYTES) -> UploadedFile:
    return UploadedFile(name=name, size_bytes=size_bytes)

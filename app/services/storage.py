"""Local filesystem storage for uploaded document packages."""

import re
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

# Characters that are unsafe or awkward in stored filenames.
_UNSAFE_CHARS = re.compile(r'[<>:"|?*\\/\x00-\x1f]')


@dataclass(frozen=True)
class StoredFile:
    """Result of writing one uploaded file to disk."""

    original_name: str
    """Client-provided filename (kept for DB / API responses)."""

    stored_name: str
    """Sanitized basename actually written under the check directory."""

    storage_path: str
    """Path relative to UPLOAD_DIR, e.g. ``{check_id}/{stored_name}``."""

    absolute_path: Path
    """Resolved absolute path of the written file."""

    size_bytes: int


class LocalFileStorage:
    """
    Save uploaded files under ``UPLOAD_DIR/{check_id}/``.

    Database rows store only metadata (including ``storage_path``);
    this class owns the on-disk layout.
    """

    def __init__(self, upload_dir: str | Path) -> None:
        self._root = Path(upload_dir).expanduser().resolve()

    @property
    def root(self) -> Path:
        return self._root

    def ensure_root(self) -> None:
        """Create the upload root directory if it does not exist."""
        self._root.mkdir(parents=True, exist_ok=True)

    def check_dir(self, check_id: uuid.UUID | str) -> Path:
        """Absolute path of the directory for a given check."""
        return self._root / str(check_id)

    def ensure_check_dir(self, check_id: uuid.UUID | str) -> Path:
        """Create ``UPLOAD_DIR/{check_id}/`` and return its absolute path."""
        self.ensure_root()
        path = self.check_dir(check_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_bytes(
        self,
        check_id: uuid.UUID | str,
        filename: str,
        data: bytes,
    ) -> StoredFile:
        """
        Write ``data`` into the check directory.

        The original filename is sanitized (path segments stripped, unsafe
        characters replaced). If a file with the same stored name already
        exists, a numeric suffix is appended before the extension.
        """
        directory = self.ensure_check_dir(check_id)
        stored_name = self._unique_name(directory, self._safe_filename(filename))
        absolute_path = directory / stored_name
        absolute_path.write_bytes(data)

        return StoredFile(
            original_name=filename,
            stored_name=stored_name,
            storage_path=f"{check_id}/{stored_name}",
            absolute_path=absolute_path,
            size_bytes=len(data),
        )

    def resolve(self, storage_path: str) -> Path:
        """
        Resolve a relative ``storage_path`` to an absolute path under root.

        Raises ``ValueError`` if the path would escape the upload root
        (path-traversal guard).
        """
        candidate = (self._root / storage_path).resolve()
        try:
            candidate.relative_to(self._root)
        except ValueError as exc:
            raise ValueError(
                f"storage_path escapes upload root: {storage_path!r}"
            ) from exc
        return candidate

    def delete_check(self, check_id: uuid.UUID | str) -> None:
        """Remove the check directory and all files inside it (best-effort cleanup)."""
        path = self.check_dir(check_id)
        if path.exists():
            shutil.rmtree(path)

    @staticmethod
    def _safe_filename(filename: str) -> str:
        """
        Reduce a client filename to a single safe basename.

        Strips directory components (``../``, absolute paths) and replaces
        characters that are problematic on common filesystems.
        """
        name = Path(filename.replace("\\", "/")).name.strip()
        name = _UNSAFE_CHARS.sub("_", name)
        name = name.strip(" .")
        if not name or name in {".", ".."}:
            return "unnamed"
        return name

    @staticmethod
    def _unique_name(directory: Path, filename: str) -> str:
        """Return ``filename``, or ``stem_N.ext`` if that name is already taken."""
        candidate = directory / filename
        if not candidate.exists():
            return filename

        stem = Path(filename).stem
        suffix = Path(filename).suffix
        index = 1
        while True:
            alternate = f"{stem}_{index}{suffix}"
            if not (directory / alternate).exists():
                return alternate
            index += 1

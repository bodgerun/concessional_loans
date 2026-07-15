"""Shared FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.services.check_service import CheckService
from app.services.storage import LocalFileStorage

SettingsDep = Annotated[Settings, Depends(get_settings)]
DbDep = Annotated[Session, Depends(get_db)]


def get_storage(settings: SettingsDep) -> LocalFileStorage:
    """Local filesystem storage rooted at UPLOAD_DIR."""
    return LocalFileStorage(settings.upload_dir)


StorageDep = Annotated[LocalFileStorage, Depends(get_storage)]


def get_check_service(db: DbDep, storage: StorageDep) -> CheckService:
    """Orchestration service for check create/list/get."""
    return CheckService(db, storage)


CheckServiceDep = Annotated[CheckService, Depends(get_check_service)]

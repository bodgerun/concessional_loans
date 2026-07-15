"""HTTP endpoints for document package checks."""

import uuid
from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile, status

from app.api.deps import CheckServiceDep
from app.api.errors import bad_request, not_found
from app.api.mappers import check_to_detail, check_to_list_item
from app.domain.package import Program
from app.schemas.checks import CheckDetailOut, CheckListItemOut
from app.schemas.errors import ErrorOut
from app.services.check_service import IncomingFile

router = APIRouter(prefix="/api/checks", tags=["checks"])

ProgramForm = Annotated[Program, Form(description="federal or regional")]
# Optional at the framework level so missing uploads become our 400, not FastAPI's 422.
FilesUpload = Annotated[
    list[UploadFile] | None,
    File(description="Document package files"),
]

_ERROR_400 = {
    "model": ErrorOut,
    "description": "Bad request (e.g. no files uploaded)",
}
_ERROR_404 = {
    "model": ErrorOut,
    "description": "Check not found",
}
_ERROR_422 = {
    "model": ErrorOut,
    "description": "Validation error (invalid program, UUID, or form fields)",
}


@router.post(
    "",
    response_model=CheckDetailOut,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document package and run a check",
    responses={
        status.HTTP_400_BAD_REQUEST: _ERROR_400,
        status.HTTP_422_UNPROCESSABLE_CONTENT: _ERROR_422,
    },
)
async def create_check(
    program: ProgramForm,
    service: CheckServiceDep,
    files: FilesUpload = None,
) -> CheckDetailOut:
    if not files:
        raise bad_request("At least one file is required")

    incoming: list[IncomingFile] = []
    for upload in files:
        content = await upload.read()
        incoming.append(
            IncomingFile(
                filename=upload.filename or "unnamed",
                content=content,
                content_type=upload.content_type,
            )
        )

    check = service.create_check(program, incoming)
    return check_to_detail(check)


@router.get(
    "",
    response_model=list[CheckListItemOut],
    summary="List all checks",
)
def list_checks(service: CheckServiceDep) -> list[CheckListItemOut]:
    return [check_to_list_item(check) for check in service.list_checks()]


@router.get(
    "/{check_id}",
    response_model=CheckDetailOut,
    summary="Get a check by id",
    responses={
        status.HTTP_404_NOT_FOUND: _ERROR_404,
        status.HTTP_422_UNPROCESSABLE_CONTENT: _ERROR_422,
    },
)
def get_check(check_id: uuid.UUID, service: CheckServiceDep) -> CheckDetailOut:
    check = service.get_check(check_id)
    if check is None:
        raise not_found(f"Check {check_id} not found")
    return check_to_detail(check)

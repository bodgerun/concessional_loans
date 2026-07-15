"""Shared error response schemas for OpenAPI documentation."""

from typing import Any

from pydantic import BaseModel, Field


class ErrorOut(BaseModel):
    """Body returned for 400/404 (and documented alongside FastAPI's 422)."""

    detail: str | list[Any] = Field(
        description="Error message, or a list of validation errors for 422",
    )

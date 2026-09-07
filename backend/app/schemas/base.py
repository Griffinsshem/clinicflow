"""
Pydantic → API envelope adapter.

One place converts ValidationError into {"errors": {"field": "..."}},
so route handlers never build error payloads by hand and the shape
cannot drift between endpoints.
"""

from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict, ValidationError

from app.utils.errors import ApiError

T = TypeVar("T", bound=BaseModel)


class StrictModel(BaseModel):
    """
    Base for every request schema.

    extra="forbid" rejects unrecognised fields outright rather than
    ignoring them. A typo'd field name becomes a visible 422 instead of
    a silently dropped value, and a client cannot smuggle attributes
    like `role` or `clinic_id` into a payload hoping something
    downstream reads them.

    str_strip_whitespace normalises input at the boundary so " a@b.com "
    and "a@b.com" cannot become two different accounts.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


def _field_path(error: dict[str, Any]) -> str:
    location = [str(part) for part in error["loc"] if part != "body"]
    return ".".join(location) or "_"


def parse_request(schema: type[T], payload: Any) -> T:
    """
    Validate a request body, raising ApiError(422) on failure.

    422 rather than 400: the request was well-formed JSON that failed
    semantic validation, which is exactly what 422 describes.
    """
    if payload is None or not isinstance(payload, dict):
        raise ApiError("Request body must be a JSON object.", 400)

    try:
        return schema.model_validate(payload)
    except ValidationError as exc:
        errors: dict[str, str] = {}
        for error in exc.errors():
            field = _field_path(error)
            errors.setdefault(field, error["msg"])
        raise ApiError("Validation failed", 422, errors) from exc


import email_validator

email_validator.TEST_ENVIRONMENT = True

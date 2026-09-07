"""Request schemas for the authentication endpoints."""

from pydantic import EmailStr, Field, field_validator

from app.schemas.base import StrictModel

PASSWORD_MIN_LENGTH = 10
PASSWORD_MAX_LENGTH = 128


class RegisterSchema(StrictModel):
    """
    Creates a clinic and its first admin together.

    Note what is absent: no `role` and no `clinic_id`. Both are assigned
    by the server. Accepting either would let a caller register straight
    into an existing clinic or grant themselves admin.
    """

    clinic_name: str = Field(min_length=2, max_length=120)
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)

    @field_validator("password")
    @classmethod
    def reject_whitespace_only(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Password cannot be blank")
        return value

    @field_validator("clinic_name", "full_name")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("This field cannot be blank")
        return value


class LoginSchema(StrictModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(max_length=PASSWORD_MAX_LENGTH)

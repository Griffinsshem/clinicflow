from datetime import date

from pydantic import EmailStr, Field, field_validator

from app.models.enums import Gender
from app.schemas.base import StrictModel

PHONE_MAX_LENGTH = 32


class PatientCreateSchema(StrictModel):
    full_name: str = Field(min_length=2, max_length=120)
    date_of_birth: date | None = None
    gender: Gender | None = None
    phone: str | None = Field(default=None, max_length=PHONE_MAX_LENGTH)
    email: EmailStr | None = Field(default=None, max_length=255)

    @field_validator("full_name")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Name cannot be blank")
        return value

    @field_validator("date_of_birth")
    @classmethod
    def reject_future_dates(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return value

    @field_validator("phone", "email", mode="before")
    @classmethod
    def empty_string_to_none(cls, value):
        if isinstance(value, str) and not value.strip():
            return None
        return value


class PatientUpdateSchema(PatientCreateSchema):

    full_name: str | None = Field(default=None, min_length=2, max_length=120)

    def changed_fields(self) -> dict:
        """Only fields the client actually sent — unset keys are ignored."""
        return self.model_dump(exclude_unset=True)

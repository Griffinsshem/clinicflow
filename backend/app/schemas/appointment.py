from datetime import datetime

from pydantic import Field, field_validator

from app.models.enums import AppointmentStatus, AppointmentType
from app.schemas.base import StrictModel

NOTES_MAX_LENGTH = 1000


class AppointmentCreateSchema(StrictModel):
    patient_id: int = Field(gt=0)
    scheduled_at: datetime
    appointment_type: AppointmentType = AppointmentType.CONSULTATION
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    notes: str | None = Field(default=None, max_length=NOTES_MAX_LENGTH)

    @field_validator("scheduled_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "Include a timezone offset, e.g. 2026-09-10T14:00:00+03:00"
            )
        return value

    @field_validator("notes", mode="before")
    @classmethod
    def empty_string_to_none(cls, value):
        if isinstance(value, str) and not value.strip():
            return None
        return value


class AppointmentUpdateSchema(StrictModel):

    scheduled_at: datetime | None = None
    appointment_type: AppointmentType | None = None
    status: AppointmentStatus | None = None
    notes: str | None = Field(default=None, max_length=NOTES_MAX_LENGTH)

    _require_timezone = field_validator("scheduled_at")(
        AppointmentCreateSchema.require_timezone.__func__
    )

    @field_validator("notes", mode="before")
    @classmethod
    def empty_string_to_none(cls, value):
        if isinstance(value, str) and not value.strip():
            return None
        return value

    def changed_fields(self) -> dict:
        return self.model_dump(exclude_unset=True)

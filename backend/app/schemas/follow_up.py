from datetime import date, datetime

from pydantic import Field, field_validator

from app.models.enums import AppointmentType, FollowUpStatus
from app.schemas.base import StrictModel

REASON_MAX_LENGTH = 500


class FollowUpCreateSchema(StrictModel):
    patient_id: int = Field(gt=0)
    follow_up_date: date
    reason: str = Field(min_length=3, max_length=REASON_MAX_LENGTH)

    appointment_id: int | None = Field(default=None, gt=0)

    @field_validator("reason")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Reason cannot be blank")
        return value


class FollowUpUpdateSchema(StrictModel):

    follow_up_date: date | None = None
    reason: str | None = Field(default=None, min_length=3, max_length=REASON_MAX_LENGTH)
    status: FollowUpStatus | None = None

    def changed_fields(self) -> dict:
        return self.model_dump(exclude_unset=True)


class FollowUpCompleteSchema(StrictModel):

    scheduled_at: datetime | None = None
    appointment_type: AppointmentType = AppointmentType.FOLLOW_UP
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("scheduled_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError(
                "Include a timezone offset, e.g. 2026-09-10T14:00:00+03:00"
            )
        return value

"""
Scheduled visits.

Note the composite foreign key: this is the structural half of clinic
isolation, and it is worth reading closely.
"""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, enum_column
from app.models.enums import AppointmentStatus, AppointmentType


class Appointment(BaseModel):
    __tablename__ = "appointments"

    clinic_id: Mapped[int] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
    )
    patient_id: Mapped[int] = mapped_column(nullable=False)

    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    appointment_type: Mapped[AppointmentType] = enum_column(
        AppointmentType, nullable=False, default=AppointmentType.CONSULTATION
    )
    status: Mapped[AppointmentStatus] = enum_column(
        AppointmentStatus, nullable=False, default=AppointmentStatus.SCHEDULED
    )
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    patient: Mapped["Patient"] = relationship(back_populates="appointments")
    follow_ups: Mapped[list["FollowUp"]] = relationship(back_populates="appointment")

    __table_args__ = (
        ForeignKeyConstraint(
            ["patient_id", "clinic_id"],
            ["patients.id", "patients.clinic_id"],
            ondelete="CASCADE",
            name="fk_appointments_patient_clinic",
        ),
        UniqueConstraint("id", "clinic_id", name="uq_appointments_id_clinic"),
        Index("ix_appointments_clinic_scheduled", "clinic_id", "scheduled_at"),
        Index("ix_appointments_clinic_status", "clinic_id", "status"),
        Index("ix_appointments_patient_scheduled", "patient_id", "scheduled_at"),
    )

    def to_dict(self, include_patient: bool = False) -> dict:
        data = {
            "id": self.id,
            "clinic_id": self.clinic_id,
            "patient_id": self.patient_id,
            "scheduled_at": self.scheduled_at.isoformat(),
            "appointment_type": self.appointment_type.value,
            "status": self.status.value,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
        }
        if include_patient and self.patient is not None:
            data["patient"] = {
                "id": self.patient.id,
                "full_name": self.patient.full_name,
                "phone": self.patient.phone,
            }
        return data

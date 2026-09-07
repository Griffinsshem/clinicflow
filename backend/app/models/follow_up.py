"""
Follow-ups: the commitment to see a patient again by a given date.

This is the model that carries the product's core value — it is the
thing clinics currently lose track of on paper.
"""

from datetime import date

from sqlalchemy import Date, ForeignKey, ForeignKeyConstraint, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, enum_column
from app.models.enums import FollowUpStatus


class FollowUp(BaseModel):
    __tablename__ = "follow_ups"

    clinic_id: Mapped[int] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
    )
    patient_id: Mapped[int] = mapped_column(nullable=False)

    appointment_id: Mapped[int | None] = mapped_column(nullable=True)

    follow_up_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[FollowUpStatus] = enum_column(
        FollowUpStatus, nullable=False, default=FollowUpStatus.UPCOMING
    )

    patient: Mapped["Patient"] = relationship(
        back_populates="follow_ups", viewonly=True
    )
    appointment: Mapped["Appointment | None"] = relationship(
        back_populates="follow_ups", viewonly=True
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["patient_id", "clinic_id"],
            ["patients.id", "patients.clinic_id"],
            ondelete="CASCADE",
            name="fk_follow_ups_patient_clinic",
        ),
        ForeignKeyConstraint(
            ["appointment_id", "clinic_id"],
            ["appointments.id", "appointments.clinic_id"],
        ondelete="SET NULL (appointment_id)",
            name="fk_follow_ups_appointment_clinic",
        ),
        Index("ix_follow_ups_clinic_status_date", "clinic_id", "status", "follow_up_date"),
        Index("ix_follow_ups_patient", "patient_id"),
    )

    def is_overdue(self, today: date | None = None) -> bool:
        """
        Derived, never stored — see FollowUpStatus for the reasoning.
        Accepts an injectable `today` so tests can assert boundary
        behaviour without freezing the system clock.
        """
        reference = today or date.today()
        return self.status == FollowUpStatus.UPCOMING and self.follow_up_date < reference

    def to_dict(self, today: date | None = None, include_patient: bool = False) -> dict:
        reference = today or date.today()
        overdue = self.is_overdue(reference)
        data = {
            "id": self.id,
            "clinic_id": self.clinic_id,
            "patient_id": self.patient_id,
            "appointment_id": self.appointment_id,
            "follow_up_date": self.follow_up_date.isoformat(),
            "reason": self.reason,
            "status": self.status.value,
            "is_overdue": overdue,
            "is_due_today": (
                self.status == FollowUpStatus.UPCOMING
                and self.follow_up_date == reference
            ),
            "created_at": self.created_at.isoformat(),
        }
        if include_patient and self.patient is not None:
            data["patient"] = {
                "id": self.patient.id,
                "full_name": self.patient.full_name,
                "phone": self.patient.phone,
            }
        return data

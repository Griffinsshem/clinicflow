"""
Patient records.

Scope is deliberately minimal — identification, contact, scheduling.
No diagnoses, no clinical notes, no medical history. That is a product
decision, not an omission: storing less means a pilot deployment carries
far less regulatory weight, and the schema can be extended later behind
proper compliance controls.
"""

from datetime import date

from sqlalchemy import Date, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, enum_column
from app.models.enums import Gender


class Patient(BaseModel):
    __tablename__ = "patients"

    clinic_id: Mapped[int] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[Gender | None] = enum_column(Gender, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)

    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    clinic: Mapped["Clinic"] = relationship(back_populates="patients")
    appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan", passive_deletes=True
    )
    follow_ups: Mapped[list["FollowUp"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan", passive_deletes=True
    )

    __table_args__ = (
        UniqueConstraint("id", "clinic_id", name="uq_patients_id_clinic"),
        Index("ix_patients_clinic_name", "clinic_id", "full_name"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "clinic_id": self.clinic_id,
            "full_name": self.full_name,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "gender": self.gender.value if self.gender else None,
            "phone": self.phone,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
        }

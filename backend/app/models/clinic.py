"""The tenant boundary. Every other record hangs off a clinic."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Clinic(BaseModel):
    __tablename__ = "clinics"

    name: Mapped[str] = mapped_column(String(120), nullable=False)

    users: Mapped[list["User"]] = relationship(
        back_populates="clinic", cascade="all, delete-orphan", passive_deletes=True
    )
    patients: Mapped[list["Patient"]] = relationship(
        back_populates="clinic", cascade="all, delete-orphan", passive_deletes=True
    )

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name}

"""
Clinic staff accounts.

The password hash never leaves this module in serialised form: to_dict()
has no branch that can emit it, so there is no flag to accidentally set
wrong at a call site.
"""

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app.models.base import BaseModel, enum_column
from app.models.enums import UserRole


class User(BaseModel):
    __tablename__ = "users"

    clinic_id: Mapped[int] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[UserRole] = enum_column(
        UserRole, nullable=False, default=UserRole.STAFF
    )

    clinic: Mapped["Clinic"] = relationship(back_populates="users")

    __table_args__ = (Index("ix_users_clinic_id", "clinic_id"),)

    def set_password(self, raw_password: str) -> None:
        """
        Werkzeug's scrypt: memory-hard, salted per call, and bundled with
        Flask so it costs us no extra dependency. The cost parameters are
        Werkzeug's current defaults.
        """
        self.password_hash = generate_password_hash(raw_password, method="scrypt")

    def check_password(self, raw_password: str) -> bool:
        """Constant-time comparison, courtesy of Werkzeug."""
        return check_password_hash(self.password_hash, raw_password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "clinic_id": self.clinic_id,
            "full_name": self.full_name,
            "email": self.email,
            "role": self.role.value,
            "created_at": self.created_at.isoformat(),
        }

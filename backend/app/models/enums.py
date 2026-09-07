"""
Domain enumerations — the single source of truth for every constrained
value in the system.

These classes are reused three times over: SQLAlchemy renders them as
CHECK constraints, Pydantic validates request bodies against them, and
the values are what the API emits. One definition, no drift between
database, validation layer, and wire format.

Inheriting from `str` means a member compares equal to its value, so
`appointment.status == "completed"` works and json.dumps() needs no
custom encoder.
"""

from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"  
    STAFF = "staff"    


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNDISCLOSED = "undisclosed" 


class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class AppointmentType(str, Enum):
    CONSULTATION = "consultation"
    CHECK_UP = "check_up"
    FOLLOW_UP = "follow_up"
    OTHER = "other"


class FollowUpStatus(str, Enum):
    """
    Only these two are ever persisted.

    `overdue` is deliberately absent: it is a function of the current
    date, not a fact about the row. Storing it would require a scheduled
    job and would be wrong between runs. It is computed on read — see
    FollowUp.is_overdue — and still surfaces in API responses.
    """

    UPCOMING = "upcoming"
    COMPLETED = "completed"


def enum_values(enum_cls: type[Enum]) -> list[str]:
    """Used by SQLAlchemy to emit the CHECK constraint value list."""
    return [member.value for member in enum_cls]

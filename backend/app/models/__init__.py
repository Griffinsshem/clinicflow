"""
Model registry.

Alembic can only autogenerate migrations for tables it has seen, and it
only sees a model once its module has been imported. Importing every
model here — and importing this package from create_app() — means a new
model is never silently missed by a migration.
"""

from app.models.appointment import Appointment
from app.models.clinic import Clinic
from app.models.follow_up import FollowUp
from app.models.patient import Patient
from app.models.user import User

__all__ = ["Appointment", "Clinic", "FollowUp", "Patient", "User"]

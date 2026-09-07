"""
Authentication business logic.

Deliberately free of Flask request/response objects: these functions
take plain arguments and raise ApiError. That keeps them unit-testable
without a request context and keeps route handlers thin.
"""

from sqlalchemy import func, select
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models.clinic import Clinic
from app.models.enums import UserRole
from app.models.user import User
from app.utils.errors import ApiError

_DUMMY_HASH = generate_password_hash("timing-equalisation-placeholder", method="scrypt")

_INVALID_CREDENTIALS = "Incorrect email or password."


def normalise_email(email: str) -> str:
    
    return email.strip().lower()


def register_clinic_with_admin(
    clinic_name: str, full_name: str, email: str, password: str
) -> tuple[Clinic, User]:
    
    email = normalise_email(email)

    existing = db.session.scalar(
        select(User.id).where(func.lower(User.email) == email).limit(1)
    )
    if existing is not None:
        raise ApiError(
            "An account with this email already exists.",
            409,
            {"email": "This email is already registered."},
        )

    clinic = Clinic(name=clinic_name.strip())
    db.session.add(clinic)
    db.session.flush()

    user = User(
        clinic_id=clinic.id,
        full_name=full_name.strip(),
        email=email,
        role=UserRole.ADMIN,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return clinic, user


def authenticate_user(email: str, password: str) -> User:
    email = normalise_email(email)
    user = db.session.scalar(select(User).where(func.lower(User.email) == email))

    if user is None:
        User(password_hash=_DUMMY_HASH).check_password(password)
        raise ApiError(_INVALID_CREDENTIALS, 401)

    if not user.check_password(password):
        raise ApiError(_INVALID_CREDENTIALS, 401)

    return user

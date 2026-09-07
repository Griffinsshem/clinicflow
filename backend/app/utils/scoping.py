from typing import TypeVar

from flask import g
from sqlalchemy import Select, select

from app.extensions import db
from app.utils.errors import ApiError

T = TypeVar("T")


def current_clinic_id() -> int:
    clinic_id = getattr(g, "clinic_id", None)
    if clinic_id is None:
        raise RuntimeError(
            "current_clinic_id() called outside an authenticated request. "
            "Did the route forget @auth_required?"
        )
    return clinic_id


def scoped_query(model: type[T]) -> Select:
    return select(model).where(model.clinic_id == current_clinic_id())


def get_scoped_or_404(model: type[T], record_id: int, label: str = "Record") -> T:
    record = db.session.scalar(
        select(model).where(model.id == record_id, model.clinic_id == current_clinic_id())
    )
    if record is None:
        raise ApiError(f"{label} not found.", 404)
    return record

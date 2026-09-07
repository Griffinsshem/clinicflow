from datetime import date

from sqlalchemy import Select, and_, or_
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.appointment import Appointment
from app.models.enums import FollowUpStatus
from app.models.follow_up import FollowUp
from app.models.patient import Patient
from app.utils.errors import ApiError
from app.utils.pagination import paginate
from app.utils.scoping import current_clinic_id, get_scoped_or_404, scoped_query


def _base_query() -> Select:
    return scoped_query(FollowUp).options(selectinload(FollowUp.patient))


def _apply_filters(stmt: Select, filters: dict, today: date) -> Select:
    if patient_id := filters.get("patient_id"):
        stmt = stmt.where(FollowUp.patient_id == patient_id)

    if status := filters.get("status"):
        stmt = stmt.where(FollowUp.status == status)

    if filters.get("overdue"):
        stmt = stmt.where(
            and_(
                FollowUp.status == FollowUpStatus.UPCOMING,
                FollowUp.follow_up_date < today,
            )
        )

    if date_from := filters.get("date_from"):
        stmt = stmt.where(FollowUp.follow_up_date >= date_from)

    if date_to := filters.get("date_to"):
        stmt = stmt.where(FollowUp.follow_up_date <= date_to)

    return stmt


def list_follow_ups(filters: dict, today: date, page: int, limit: int):
    stmt = _apply_filters(_base_query(), filters, today).order_by(FollowUp.follow_up_date)
    return paginate(stmt, page, limit)


def list_grouped(today: date) -> dict[str, list[dict]]:
    outstanding = db.session.scalars(
        _base_query()
        .where(FollowUp.status == FollowUpStatus.UPCOMING)
        .order_by(FollowUp.follow_up_date)
    ).all()

    completed = db.session.scalars(
        _base_query()
        .where(FollowUp.status == FollowUpStatus.COMPLETED)
        .order_by(FollowUp.follow_up_date.desc())
        .limit(20)
    ).all()

    groups: dict[str, list[dict]] = {"overdue": [], "due_today": [], "upcoming": []}
    for follow_up in outstanding:
        if follow_up.follow_up_date < today:
            groups["overdue"].append(follow_up.to_dict(today, include_patient=True))
        elif follow_up.follow_up_date == today:
            groups["due_today"].append(follow_up.to_dict(today, include_patient=True))
        else:
            groups["upcoming"].append(follow_up.to_dict(today, include_patient=True))

    groups["completed"] = [f.to_dict(today, include_patient=True) for f in completed]
    return groups


def get_follow_up(follow_up_id: int) -> FollowUp:
    return get_scoped_or_404(FollowUp, follow_up_id, "Follow-up")


def create_follow_up(data: dict) -> FollowUp:
    get_scoped_or_404(Patient, data["patient_id"], "Patient")
    if data.get("appointment_id") is not None:
        get_scoped_or_404(Appointment, data["appointment_id"], "Appointment")

    follow_up = FollowUp(clinic_id=current_clinic_id(), **data)
    db.session.add(follow_up)
    db.session.commit()
    return follow_up


def update_follow_up(follow_up_id: int, changes: dict) -> FollowUp:
    follow_up = get_scoped_or_404(FollowUp, follow_up_id, "Follow-up")
    for field, value in changes.items():
        setattr(follow_up, field, value)
    db.session.commit()
    return follow_up


def complete_follow_up(
    follow_up_id: int, next_appointment: dict | None
) -> tuple[FollowUp, Appointment | None]:
    follow_up = get_scoped_or_404(FollowUp, follow_up_id, "Follow-up")

    if follow_up.status == FollowUpStatus.COMPLETED:
        raise ApiError("This follow-up is already completed.", 409)

    follow_up.status = FollowUpStatus.COMPLETED

    appointment = None
    if next_appointment and next_appointment.get("scheduled_at"):
        appointment = Appointment(
            clinic_id=current_clinic_id(),
            patient_id=follow_up.patient_id,
            scheduled_at=next_appointment["scheduled_at"],
            appointment_type=next_appointment["appointment_type"],
            notes=next_appointment.get("notes"),
        )
        db.session.add(appointment)

    db.session.commit()
    return follow_up, appointment


def list_for_patient(patient_id: int, today: date) -> list[dict]:
    get_scoped_or_404(Patient, patient_id, "Patient")
    stmt = (
        scoped_query(FollowUp)
        .where(FollowUp.patient_id == patient_id)
        .order_by(FollowUp.follow_up_date.desc())
    )
    return [f.to_dict(today) for f in db.session.scalars(stmt).all()]

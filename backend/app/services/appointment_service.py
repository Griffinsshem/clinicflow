from datetime import datetime

from sqlalchemy import Select
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.appointment import Appointment
from app.models.enums import AppointmentStatus, AppointmentType
from app.models.patient import Patient
from app.utils.errors import ApiError
from app.utils.pagination import paginate
from app.utils.scoping import current_clinic_id, get_scoped_or_404, scoped_query

ALLOWED_TRANSITIONS: dict[AppointmentStatus, set[AppointmentStatus]] = {
    AppointmentStatus.SCHEDULED: {
        AppointmentStatus.CONFIRMED,
        AppointmentStatus.COMPLETED,
        AppointmentStatus.CANCELLED,
        AppointmentStatus.NO_SHOW,
    },
    AppointmentStatus.CONFIRMED: {
        AppointmentStatus.COMPLETED,
        AppointmentStatus.CANCELLED,
        AppointmentStatus.NO_SHOW,
    },
    AppointmentStatus.COMPLETED: set(),
    AppointmentStatus.CANCELLED: set(),
    AppointmentStatus.NO_SHOW: {AppointmentStatus.SCHEDULED},  # rebooking
}


def _verify_patient(patient_id: int) -> Patient:
    return get_scoped_or_404(Patient, patient_id, "Patient")


def _apply_filters(stmt: Select, filters: dict) -> Select:
    if patient_id := filters.get("patient_id"):
        stmt = stmt.where(Appointment.patient_id == patient_id)

    if status := filters.get("status"):
        stmt = stmt.where(Appointment.status == status)

    if appointment_type := filters.get("appointment_type"):
        stmt = stmt.where(Appointment.appointment_type == appointment_type)

    if date_from := filters.get("date_from"):
        stmt = stmt.where(Appointment.scheduled_at >= date_from)

    if date_to := filters.get("date_to"):
        stmt = stmt.where(Appointment.scheduled_at <= date_to)

    return stmt


def list_appointments(filters: dict, page: int, limit: int):
    stmt = _apply_filters(scoped_query(Appointment), filters)
    stmt = stmt.options(selectinload(Appointment.patient)).order_by(
        Appointment.scheduled_at.desc()
    )
    return paginate(stmt, page, limit)


def get_appointment(appointment_id: int) -> Appointment:
    return get_scoped_or_404(Appointment, appointment_id, "Appointment")


def create_appointment(data: dict) -> Appointment:
    _verify_patient(data["patient_id"])

    appointment = Appointment(clinic_id=current_clinic_id(), **data)
    db.session.add(appointment)
    db.session.commit()
    return appointment


def update_appointment(appointment_id: int, changes: dict) -> Appointment:
    appointment = get_scoped_or_404(Appointment, appointment_id, "Appointment")

    new_status = changes.get("status")
    if new_status is not None and new_status != appointment.status:
        allowed = ALLOWED_TRANSITIONS[appointment.status]
        if new_status not in allowed:
            raise ApiError(
                f"An appointment that is {appointment.status.value} "
                f"cannot be marked {new_status.value}.",
                422,
                {"status": "This status change is not allowed."},
            )

    for field, value in changes.items():
        setattr(appointment, field, value)
    db.session.commit()
    return appointment


def delete_appointment(appointment_id: int) -> None:
    appointment = get_scoped_or_404(Appointment, appointment_id, "Appointment")
    db.session.delete(appointment)
    db.session.commit()


def list_for_patient(patient_id: int) -> list[Appointment]:
    """
    All appointments for one patient, newest first.

    Used by the patient detail page. Verifies the patient first so a
    foreign ID cannot be used to probe for appointment counts.
    """
    _verify_patient(patient_id)
    stmt = (
        scoped_query(Appointment)
        .where(Appointment.patient_id == patient_id)
        .order_by(Appointment.scheduled_at.desc())
    )
    return list(db.session.scalars(stmt).all())

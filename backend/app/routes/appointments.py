"""Appointment endpoints. Authenticated and clinic-scoped throughout."""

from flask import Blueprint, request

from app.schemas.appointment import AppointmentCreateSchema, AppointmentUpdateSchema
from app.schemas.base import parse_request
from app.schemas.filters import parse_appointment_filters
from app.services import appointment_service
from app.utils.decorators import auth_required
from app.utils.errors import ApiError
from app.utils.pagination import parse_pagination
from app.utils.responses import success_response

bp = Blueprint("appointments", __name__)


@bp.get("/appointments")
@auth_required
def list_appointments():
    page, limit = parse_pagination(request.args)
    filters = parse_appointment_filters(request.args)
    appointments, meta = appointment_service.list_appointments(filters, page, limit)
    return success_response(
        data=[a.to_dict(include_patient=True) for a in appointments], meta=meta
    )


@bp.post("/appointments")
@auth_required
def create_appointment():
    data = parse_request(AppointmentCreateSchema, request.get_json(silent=True))
    appointment = appointment_service.create_appointment(data.model_dump())
    return success_response(
        data=appointment.to_dict(include_patient=True),
        message="Appointment scheduled.",
        status_code=201,
    )


@bp.get("/appointments/<int:appointment_id>")
@auth_required
def get_appointment(appointment_id: int):
    appointment = appointment_service.get_appointment(appointment_id)
    return success_response(data=appointment.to_dict(include_patient=True))


@bp.patch("/appointments/<int:appointment_id>")
@auth_required
def update_appointment(appointment_id: int):
    data = parse_request(AppointmentUpdateSchema, request.get_json(silent=True))
    changes = data.changed_fields()
    if not changes:
        raise ApiError("No changes were provided.", 422)

    appointment = appointment_service.update_appointment(appointment_id, changes)
    return success_response(
        data=appointment.to_dict(include_patient=True), message="Appointment updated."
    )


@bp.delete("/appointments/<int:appointment_id>")
@auth_required
def delete_appointment(appointment_id: int):
    appointment_service.delete_appointment(appointment_id)
    return success_response(message="Appointment removed.")


@bp.get("/patients/<int:patient_id>/appointments")
@auth_required
def list_patient_appointments(patient_id: int):
    """Appointment history for the patient detail page."""
    appointments = appointment_service.list_for_patient(patient_id)
    return success_response(data=[a.to_dict() for a in appointments])

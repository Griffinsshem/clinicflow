from flask import Blueprint, request

from app.schemas.base import parse_request
from app.schemas.patient import PatientCreateSchema, PatientUpdateSchema
from app.services import patient_service
from app.utils.decorators import auth_required
from app.utils.errors import ApiError
from app.utils.pagination import parse_pagination
from app.utils.responses import success_response

bp = Blueprint("patients", __name__)


@bp.get("/patients")
@auth_required
def list_patients():
    page, limit = parse_pagination(request.args)
    patients, meta = patient_service.list_patients(
        search=request.args.get("search"), page=page, limit=limit
    )
    return success_response(
        data=[patient.to_dict() for patient in patients], meta=meta
    )


@bp.post("/patients")
@auth_required
def create_patient():
    data = parse_request(PatientCreateSchema, request.get_json(silent=True))
    patient = patient_service.create_patient(data.model_dump())
    return success_response(
        data=patient.to_dict(), message="Patient added.", status_code=201
    )


@bp.get("/patients/<int:patient_id>")
@auth_required
def get_patient(patient_id: int):
    patient = patient_service.get_patient(patient_id)
    return success_response(data=patient.to_dict())


@bp.patch("/patients/<int:patient_id>")
@auth_required
def update_patient(patient_id: int):
    data = parse_request(PatientUpdateSchema, request.get_json(silent=True))
    changes = data.changed_fields()
    if not changes:
        raise ApiError("No changes were provided.", 422)

    patient = patient_service.update_patient(patient_id, changes)
    return success_response(data=patient.to_dict(), message="Patient updated.")


@bp.delete("/patients/<int:patient_id>")
@auth_required
def delete_patient(patient_id: int):
    patient_service.delete_patient(patient_id)
    return success_response(message="Patient removed.")

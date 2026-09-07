from sqlalchemy import Select, or_

from app.extensions import db
from app.models.patient import Patient
from app.utils.pagination import escape_like, paginate
from app.utils.scoping import current_clinic_id, get_scoped_or_404, scoped_query


def _apply_search(stmt: Select, search: str | None) -> Select:
    if not search or not search.strip():
        return stmt

    pattern = f"%{escape_like(search.strip())}%"
    return stmt.where(
        or_(
            Patient.full_name.ilike(pattern, escape="\\"),
            Patient.phone.ilike(pattern, escape="\\"),
            Patient.email.ilike(pattern, escape="\\"),
        )
    )


def list_patients(search: str | None, page: int, limit: int) -> tuple[list[Patient], dict]:
    stmt = _apply_search(scoped_query(Patient), search).order_by(Patient.full_name)
    return paginate(stmt, page, limit)


def get_patient(patient_id: int) -> Patient:
    return get_scoped_or_404(Patient, patient_id, "Patient")


def create_patient(data: dict) -> Patient:
    patient = Patient(clinic_id=current_clinic_id(), **data)
    db.session.add(patient)
    db.session.commit()
    return patient


def update_patient(patient_id: int, changes: dict) -> Patient:
    patient = get_scoped_or_404(Patient, patient_id, "Patient")
    for field, value in changes.items():
        setattr(patient, field, value)
    db.session.commit()
    return patient


def delete_patient(patient_id: int) -> None:
    patient = get_scoped_or_404(Patient, patient_id, "Patient")
    db.session.delete(patient)
    db.session.commit()

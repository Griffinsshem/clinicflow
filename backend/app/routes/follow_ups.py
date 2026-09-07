from flask import Blueprint, request

from app.schemas.base import parse_request
from app.schemas.filters import parse_follow_up_filters
from app.schemas.follow_up import (
    FollowUpCompleteSchema,
    FollowUpCreateSchema,
    FollowUpUpdateSchema,
)
from app.services import follow_up_service
from app.utils.dates import clinic_today
from app.utils.decorators import auth_required
from app.utils.errors import ApiError
from app.utils.pagination import parse_pagination
from app.utils.responses import success_response

bp = Blueprint("follow_ups", __name__)


def _today():
    return clinic_today(request.args.get("tz_offset"))


@bp.get("/follow-ups")
@auth_required
def list_follow_ups():
    today = _today()

    if request.args.get("grouped", "").lower() in {"1", "true", "yes"}:
        return success_response(data=follow_up_service.list_grouped(today))

    page, limit = parse_pagination(request.args)
    filters = parse_follow_up_filters(request.args)
    follow_ups, meta = follow_up_service.list_follow_ups(filters, today, page, limit)
    return success_response(
        data=[f.to_dict(today, include_patient=True) for f in follow_ups], meta=meta
    )


@bp.post("/follow-ups")
@auth_required
def create_follow_up():
    data = parse_request(FollowUpCreateSchema, request.get_json(silent=True))
    follow_up = follow_up_service.create_follow_up(data.model_dump())
    return success_response(
        data=follow_up.to_dict(_today(), include_patient=True),
        message="Follow-up created.",
        status_code=201,
    )


@bp.patch("/follow-ups/<int:follow_up_id>")
@auth_required
def update_follow_up(follow_up_id: int):
    data = parse_request(FollowUpUpdateSchema, request.get_json(silent=True))
    changes = data.changed_fields()
    if not changes:
        raise ApiError("No changes were provided.", 422)

    follow_up = follow_up_service.update_follow_up(follow_up_id, changes)
    return success_response(
        data=follow_up.to_dict(_today(), include_patient=True),
        message="Follow-up updated.",
    )


@bp.post("/follow-ups/<int:follow_up_id>/complete")
@auth_required
def complete_follow_up(follow_up_id: int):
    data = parse_request(FollowUpCompleteSchema, request.get_json(silent=True) or {})
    follow_up, appointment = follow_up_service.complete_follow_up(
        follow_up_id, data.model_dump()
    )

    return success_response(
        data={
            "follow_up": follow_up.to_dict(_today(), include_patient=True),
            "appointment": appointment.to_dict() if appointment else None,
        },
        message=(
            "Follow-up completed and next appointment scheduled."
            if appointment
            else "Follow-up completed."
        ),
    )


@bp.get("/patients/<int:patient_id>/follow-ups")
@auth_required
def list_patient_follow_ups(patient_id: int):
    return success_response(
        data=follow_up_service.list_for_patient(patient_id, _today())
    )

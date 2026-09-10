from flask import Blueprint, current_app, request

from app.extensions import limiter
from app.services.demo_service import create_demo_clinic
from app.utils.dates import MAX_OFFSET_MINUTES
from app.utils.errors import ApiError
from app.utils.responses import success_response

bp = Blueprint("demo", __name__)


def _offset_minutes() -> int:
    try:
        offset = int(request.args.get("tz_offset", 0))
    except (TypeError, ValueError):
        return 0
    return offset if abs(offset) <= MAX_OFFSET_MINUTES else 0


@bp.post("/demo")
@limiter.limit("3 per hour")
def create_demo():
    if not current_app.config["DEMO_ENABLED"]:
        raise ApiError("Demo access is not available.", 404)

    clinic, user, _password = create_demo_clinic(_offset_minutes())

    from flask_jwt_extended import create_access_token

    token = create_access_token(
        identity=str(user.id),
        additional_claims={"clinic_id": user.clinic_id, "role": user.role.value},
    )

    current_app.logger.info("Demo clinic created: clinic_id=%s", clinic.id)

    return success_response(
        data={
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": int(
                current_app.config["JWT_ACCESS_TOKEN_EXPIRES"].total_seconds()
            ),
            "user": user.to_dict(),
            "clinic": clinic.to_dict(),
        },
        message="Demo clinic ready.",
        status_code=201,
    )

from flask import Blueprint, request

from app.services import dashboard_service
from app.utils.dates import MAX_OFFSET_MINUTES, clinic_today
from app.utils.decorators import auth_required
from app.utils.responses import success_response

bp = Blueprint("dashboard", __name__)


def _offset_minutes() -> int:
    try:
        offset = int(request.args.get("tz_offset", 0))
    except (TypeError, ValueError):
        return 0
    return offset if abs(offset) <= MAX_OFFSET_MINUTES else 0


@bp.get("/dashboard")
@auth_required
def get_dashboard():
    offset = _offset_minutes()
    return success_response(
        data=dashboard_service.build_dashboard(clinic_today(offset), offset)
    )

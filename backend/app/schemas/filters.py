from datetime import datetime

from app.models.enums import AppointmentStatus, AppointmentType
from app.utils.errors import ApiError


def _parse_enum(value: str | None, enum_cls, field: str):
    if value is None or value == "":
        return None
    try:
        return enum_cls(value)
    except ValueError:
        allowed = ", ".join(member.value for member in enum_cls)
        raise ApiError(
            "Invalid filter value.", 422, {field: f"Must be one of: {allowed}"}
        ) from None


def _parse_datetime(value: str | None, field: str) -> datetime | None:
    if value is None or value == "":
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise ApiError(
            "Invalid filter value.",
            422,
            {field: "Use ISO-8601 format, e.g. 2026-09-10T00:00:00+03:00"},
        ) from None

    if parsed.tzinfo is None:
        raise ApiError(
            "Invalid filter value.", 422, {field: "Include a timezone offset."}
        )
    return parsed


def _parse_int(value: str | None, field: str) -> int | None:
    if value is None or value == "":
        return None
    try:
        parsed = int(value)
    except ValueError:
        raise ApiError("Invalid filter value.", 422, {field: "Must be a number."}) from None
    if parsed <= 0:
        raise ApiError("Invalid filter value.", 422, {field: "Must be positive."})
    return parsed


def parse_appointment_filters(args) -> dict:
    return {
        "patient_id": _parse_int(args.get("patient_id"), "patient_id"),
        "status": _parse_enum(args.get("status"), AppointmentStatus, "status"),
        "appointment_type": _parse_enum(
            args.get("appointment_type"), AppointmentType, "appointment_type"
        ),
        "date_from": _parse_datetime(args.get("date_from"), "date_from"),
        "date_to": _parse_datetime(args.get("date_to"), "date_to"),
    }


def _parse_date(value: str | None, field: str):
    from datetime import date as date_cls

    if value is None or value == "":
        return None
    try:
        return date_cls.fromisoformat(value)
    except ValueError:
        raise ApiError(
            "Invalid filter value.", 422, {field: "Use YYYY-MM-DD format."}
        ) from None


def parse_follow_up_filters(args) -> dict:
    from app.models.enums import FollowUpStatus

    return {
        "patient_id": _parse_int(args.get("patient_id"), "patient_id"),
        "status": _parse_enum(args.get("status"), FollowUpStatus, "status"),
        "overdue": args.get("overdue", "").lower() in {"1", "true", "yes"},
        "date_from": _parse_date(args.get("date_from"), "date_from"),
        "date_to": _parse_date(args.get("date_to"), "date_to"),
    }

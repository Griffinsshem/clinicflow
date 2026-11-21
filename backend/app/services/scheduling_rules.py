"""
Business rules for when appointments and follow-ups may be booked,
changed, or have their status moved.

Schemas check shape (types, lengths, timezone present); these rules check
whether a value makes sense *for this record right now*, which needs the
current time and the record's existing state. They live in one module so
every path that books or changes something (create, update, complete a
follow-up and book the next visit) applies the same rules.

Each rule raises ApiError with a field error keyed by the form field it
concerns, so the frontend shows the message next to the right input.
"""

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from app.extensions import db
from app.models.appointment import Appointment
from app.models.enums import AppointmentStatus
from app.utils.errors import ApiError
from app.utils.scoping import current_clinic_id

# A booking may start up to this long ago, so a walk-in who is already
# in the chair can still be recorded as scheduled.
BOOKING_GRACE = timedelta(hours=1)

# Nothing is booked further ahead than this; a later date is almost
# always a typo (2062 instead of 2026).
MAX_BOOKING_AHEAD = timedelta(days=730)

# Past visits can be recorded (back-entry), but not decades back.
MAX_BACKDATE = timedelta(days=5 * 365)

# A visit may be marked completed slightly before its booked start,
# e.g. when the patient was seen early.
EARLY_COMPLETION_GRACE = timedelta(hours=1)

# Two active appointments for the same patient closer than this are
# treated as a double booking.
DOUBLE_BOOKING_WINDOW = timedelta(minutes=30)

ACTIVE_STATUSES = {AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED}

# Once an appointment is in one of these states, when it happened and
# what kind of visit it was are part of the record and cannot change.
# Notes stay editable, so staff can add visit notes afterwards.
LOCKED_STATUSES = {
    AppointmentStatus.COMPLETED,
    AppointmentStatus.CANCELLED,
    AppointmentStatus.NO_SHOW,
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _reject(field: str, message: str, status_code: int = 422) -> None:
    raise ApiError(message, status_code, {field: message})


def same_minute(a: datetime, b: datetime) -> bool:
    """
    True when two instants fall within the same minute.

    The edit form always re-sends the date and time, at minute precision,
    even when the user only changed the notes. Treating that as "changed"
    would wrongly trip the locked-record and date rules.
    """
    return abs(a - b) < timedelta(minutes=1)


# --- Appointments ---------------------------------------------------------


def check_booking_time(scheduled_at: datetime, status: AppointmentStatus) -> None:
    """
    Is this a sensible time for an appointment in this status?

    Upcoming appointments (scheduled, confirmed) must be in the future,
    allowing a short grace for walk-ins. Past records (completed, no-show)
    must not be in the future. Everything has outer bounds to catch typos.
    """
    now = _now()

    if scheduled_at > now + MAX_BOOKING_AHEAD:
        _reject("scheduled_at", "Appointments can be booked up to two years ahead.")
    if scheduled_at < now - MAX_BACKDATE:
        _reject("scheduled_at", "That date is too far in the past. Check the year.")

    if status in ACTIVE_STATUSES and scheduled_at < now - BOOKING_GRACE:
        _reject(
            "scheduled_at",
            "That time has already passed. Choose a time from now onwards.",
        )
    if status == AppointmentStatus.COMPLETED and scheduled_at > now + EARLY_COMPLETION_GRACE:
        _reject(
            "scheduled_at",
            "A visit in the future cannot be recorded as completed.",
        )
    if status == AppointmentStatus.NO_SHOW and scheduled_at > now:
        _reject(
            "scheduled_at",
            "A visit that hasn't started yet cannot be recorded as a no-show.",
        )


def check_status_time(appointment: Appointment, new_status: AppointmentStatus) -> None:
    """
    A status change must agree with when the visit is booked.

    Only checks the outcomes that assert the visit has happened. Moving to
    scheduled or confirmed is not time-checked here: rebooking a no-show
    keeps its old time until staff pick a new one in the edit form, where
    check_booking_time applies.
    """
    now = _now()
    if (
        new_status == AppointmentStatus.COMPLETED
        and appointment.scheduled_at > now + EARLY_COMPLETION_GRACE
    ):
        raise ApiError(
            "This visit hasn't happened yet, so it can't be marked completed.",
            422,
            {"status": "The appointment is in the future."},
        )
    if new_status == AppointmentStatus.NO_SHOW and appointment.scheduled_at > now:
        raise ApiError(
            "This visit hasn't started yet, so it can't be marked a no-show.",
            422,
            {"status": "The appointment is in the future."},
        )


def check_locked_fields(appointment: Appointment, changes: dict) -> None:
    """
    Completed, cancelled and no-show appointments keep their time and type.

    A no-show may be rebooked by moving it back to scheduled; a new time
    can be set in the same request, or afterwards.
    """
    if appointment.status not in LOCKED_STATUSES:
        return
    if (
        appointment.status == AppointmentStatus.NO_SHOW
        and changes.get("status") == AppointmentStatus.SCHEDULED
    ):
        return

    label = appointment.status.value.replace("_", "-")

    new_time = changes.get("scheduled_at")
    if new_time is not None and not same_minute(new_time, appointment.scheduled_at):
        _reject(
            "scheduled_at",
            f"This appointment is {label}, so its date and time can no longer change. "
            "Book a new appointment instead.",
        )

    new_type = changes.get("appointment_type")
    if new_type is not None and new_type != appointment.appointment_type:
        _reject(
            "appointment_type",
            f"This appointment is {label}, so its type can no longer change.",
        )


def check_double_booking(
    patient_id: int,
    scheduled_at: datetime,
    status: AppointmentStatus,
    exclude_id: int | None = None,
) -> None:
    """
    Refuse a second active appointment for the same patient at the same time.

    Scoped to one patient: different patients at the same time are normal
    in a clinic with more than one practitioner, and ClinicFlow does not
    model practitioners or rooms.
    """
    if status not in ACTIVE_STATUSES:
        return

    stmt = select(Appointment.id).where(
        Appointment.clinic_id == current_clinic_id(),
        Appointment.patient_id == patient_id,
        Appointment.status.in_(ACTIVE_STATUSES),
        Appointment.scheduled_at > scheduled_at - DOUBLE_BOOKING_WINDOW,
        Appointment.scheduled_at < scheduled_at + DOUBLE_BOOKING_WINDOW,
    )
    if exclude_id is not None:
        stmt = stmt.where(Appointment.id != exclude_id)

    if db.session.scalar(stmt.limit(1)) is not None:
        _reject(
            "scheduled_at",
            "This patient already has an appointment within 30 minutes of this time.",
            409,
        )


# --- Follow-ups -----------------------------------------------------------


def check_follow_up_date(follow_up_date: date) -> None:
    """
    A new or moved follow-up must fall between today and two years out.

    "Today" is taken one day early: the server runs on UTC, and for a
    clinic behind UTC (the Americas, in the evening) the local date can
    still be the previous UTC day. A follow-up dated in the past would be
    overdue the moment it was created, which is never intended.
    """
    today = _now().date()
    if follow_up_date < today - timedelta(days=1):
        _reject("follow_up_date", "Choose today or a later date.")
    if follow_up_date > today + MAX_BOOKING_AHEAD:
        _reject("follow_up_date", "Follow-ups can be set up to two years ahead.")

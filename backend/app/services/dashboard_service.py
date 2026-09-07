from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import Select, and_, func, select
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.appointment import Appointment
from app.models.enums import AppointmentStatus, FollowUpStatus
from app.models.follow_up import FollowUp
from app.models.patient import Patient
from app.utils.scoping import current_clinic_id, scoped_query

MAX_SCHEDULE_ROWS = 50
WEEKLY_ACTIVITY_DAYS = 7

INACTIVE_STATUSES = (AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW)


def _count(stmt: Select) -> int:
    return db.session.scalar(select(func.count()).select_from(stmt.subquery())) or 0


def _day_bounds(day: date, offset_minutes: int) -> tuple[datetime, datetime]:
    
    tz = timezone(timedelta(minutes=offset_minutes))
    start_local = datetime.combine(day, time.min, tzinfo=tz)
    return start_local, start_local + timedelta(days=1)


def build_dashboard(today: date, offset_minutes: int) -> dict:
    day_start, day_end = _day_bounds(today, offset_minutes)


    total_patients = _count(scoped_query(Patient))

    appointments_today = _count(
        scoped_query(Appointment).where(
            and_(
                Appointment.scheduled_at >= day_start,
                Appointment.scheduled_at < day_end,
                Appointment.status.not_in(INACTIVE_STATUSES),
            )
        )
    )

    upcoming_appointments = _count(
        scoped_query(Appointment).where(
            and_(
                Appointment.scheduled_at >= day_end,
                Appointment.status.not_in(INACTIVE_STATUSES),
            )
        )
    )

    follow_ups_overdue = _count(
        scoped_query(FollowUp).where(
            and_(
                FollowUp.status == FollowUpStatus.UPCOMING,
                FollowUp.follow_up_date < today,
            )
        )
    )

    follow_ups_due_today = _count(
        scoped_query(FollowUp).where(
            and_(
                FollowUp.status == FollowUpStatus.UPCOMING,
                FollowUp.follow_up_date == today,
            )
        )
    )

    return {
        "metrics": {
            "total_patients": total_patients,
            "appointments_today": appointments_today,
            "upcoming_appointments": upcoming_appointments,
            "follow_ups_overdue": follow_ups_overdue,
            "follow_ups_due_today": follow_ups_due_today,
            "follow_ups_needing_attention": follow_ups_overdue + follow_ups_due_today,
        },
        "today_schedule": _todays_schedule(day_start, day_end),
        "weekly_activity": _weekly_activity(today, offset_minutes),
        "attention_follow_ups": _attention_follow_ups(today),
    }


def _todays_schedule(day_start: datetime, day_end: datetime) -> list[dict]:
    """
    Today's appointments in chronological order.

    selectinload fetches all patients in one extra query rather than one
    per appointment — the classic N+1 that turns a 20-row list into 21
    round trips.
    """
    stmt = (
        scoped_query(Appointment)
        .where(
            and_(
                Appointment.scheduled_at >= day_start,
                Appointment.scheduled_at < day_end,
            )
        )
        .options(selectinload(Appointment.patient))
        .order_by(Appointment.scheduled_at)
        .limit(MAX_SCHEDULE_ROWS)
    )
    return [a.to_dict(include_patient=True) for a in db.session.scalars(stmt).all()]


def _weekly_activity(today: date, offset_minutes: int) -> list[dict]:
    
    start_day = today - timedelta(days=WEEKLY_ACTIVITY_DAYS - 1)
    range_start, _ = _day_bounds(start_day, offset_minutes)
    _, range_end = _day_bounds(today, offset_minutes)

    sign = "+" if offset_minutes >= 0 else "-"
    hours, minutes = divmod(abs(offset_minutes), 60)
    tz_name = f"{sign}{hours:02d}:{minutes:02d}"

    local_day = func.date(
        func.timezone(tz_name, Appointment.scheduled_at)
    ).label("day")

    stmt = (
        select(local_day, func.count().label("count"))
        .where(
            and_(
                Appointment.clinic_id == current_clinic_id(),
                Appointment.scheduled_at >= range_start,
                Appointment.scheduled_at < range_end,
                Appointment.status.not_in(INACTIVE_STATUSES),
            )
        )
        .group_by(local_day)
    )

    counts = {row.day: row.count for row in db.session.execute(stmt)}

    return [
        {
            "date": (start_day + timedelta(days=offset)).isoformat(),
            "count": counts.get(start_day + timedelta(days=offset), 0),
        }
        for offset in range(WEEKLY_ACTIVITY_DAYS)
    ]


def _attention_follow_ups(today: date) -> list[dict]:
    
    stmt = (
        scoped_query(FollowUp)
        .where(
            and_(
                FollowUp.status == FollowUpStatus.UPCOMING,
                FollowUp.follow_up_date <= today,
            )
        )
        .options(selectinload(FollowUp.patient))
        .order_by(FollowUp.follow_up_date)
        .limit(10)
    )
    return [f.to_dict(today, include_patient=True) for f in db.session.scalars(stmt).all()]

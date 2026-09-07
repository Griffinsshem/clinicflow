from datetime import date, datetime, timedelta, timezone

MAX_OFFSET_MINUTES = 14 * 60


def clinic_today(offset_minutes: str | int | None) -> date:
    """Today's date in the caller's timezone."""
    try:
        offset = int(offset_minutes) if offset_minutes is not None else 0
    except (TypeError, ValueError):
        offset = 0

    if abs(offset) > MAX_OFFSET_MINUTES:
        offset = 0

    return (datetime.now(timezone.utc) + timedelta(minutes=offset)).date()

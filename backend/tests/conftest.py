"""
Shared pytest fixtures.

Every test runs against clinicflow_test, created and dropped per
session. Nothing here can touch the development database.
"""

import itertools
from datetime import date, datetime, timedelta, timezone

import pytest

from app import create_app
from app.extensions import db as _db
from app.models.appointment import Appointment
from app.models.enums import AppointmentStatus
from app.models.follow_up import FollowUp


@pytest.fixture(scope="session")
def app():
    """
    Build the app once, but deliberately do NOT keep an app context
    pushed for the whole session.

    Flask only creates a new app context for a request if one is not
    already active. Holding a session-wide context therefore means every
    test request reuses it, teardown_appcontext never fires, and
    Flask-SQLAlchemy never removes the session — leaving a transaction
    open that holds ACCESS SHARE locks on every table it read. The
    TRUNCATE in clean_tables then blocks against those locks.

    Pushing a context only for the DDL below keeps request handling
    normal: each request gets its own context and releases its
    connection on teardown.
    """
    application = create_app("testing")

    if not application.config["SQLALCHEMY_DATABASE_URI"]:
        pytest.fail("TEST_DATABASE_URL is not set — refusing to guess a database.")

    with application.app_context():
        _db.create_all()

    yield application

    with application.app_context():
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(autouse=True)
def clean_tables(app):
    """
    Truncate between tests so each starts from an empty database.

    TRUNCATE ... CASCADE with RESTART IDENTITY is faster than
    drop/create and resets sequences, so IDs are predictable per test.

    lock_timeout is a safety net: if anything ever does hold a
    conflicting lock again, this fails in two seconds with a clear error
    instead of hanging the run indefinitely.
    """
    yield
    with app.app_context():
        _db.session.remove()
        tables = ",".join(
            f'"{table.name}"' for table in reversed(_db.metadata.sorted_tables)
        )
        _db.session.execute(_db.text("SET LOCAL lock_timeout = '2s'"))
        _db.session.execute(_db.text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
        _db.session.commit()
        _db.session.remove()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def register_clinic(client):
    """
    Registers a clinic and returns its token plus IDs.

    Rate limiting is disabled in the testing config, so this can be
    called repeatedly within one test.
    """

    def _register(
        clinic_name="Test Clinic",
        email="admin@example.com",
        password="correct-horse-battery",
    ):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "clinic_name": clinic_name,
                "full_name": "Test Admin",
                "email": email,
                "password": password,
            },
        )
        assert response.status_code == 201, response.get_json()
        body = response.get_json()["data"]
        return {
            "token": body["access_token"],
            "user_id": body["user"]["id"],
            "clinic_id": body["clinic"]["id"],
            "headers": {"Authorization": f"Bearer {body['access_token']}"},
        }

    return _register


@pytest.fixture
def two_clinics(register_clinic):
    """
    Two fully separate clinics, each with an admin and one patient.

    The backbone of every isolation test: anything clinic A can reach
    that belongs to clinic B is a security failure.
    """
    a = register_clinic(clinic_name="Clinic A", email="a@clinic-a.test")
    b = register_clinic(clinic_name="Clinic B", email="b@clinic-b.test")
    return {"a": a, "b": b}


@pytest.fixture
def make_patient(client):
    """Create a patient in the clinic owning the given auth headers."""

    def _make(session, full_name="Jane Doe", **fields):
        response = client.post(
            "/api/v1/patients",
            headers=session["headers"],
            json={"full_name": full_name, **fields},
        )
        assert response.status_code == 201, response.get_json()
        return response.get_json()["data"]

    return _make


def _direct_update(app, model, record_id, **values):
    """
    Write straight to the database, bypassing the API's business rules.

    Only for building test state the API rightly refuses to create, such
    as a follow-up that is already overdue or a visit that happened
    yesterday. The session is removed afterwards so no transaction is
    left open (see the app fixture).
    """
    with app.app_context():
        _db.session.execute(
            _db.update(model).where(model.id == record_id).values(**values)
        )
        _db.session.commit()
        _db.session.remove()


# Distinct default times, so appointments a test creates for one patient
# never trip the double-booking rule unless the test intends it.
_appointment_slots = itertools.count()


@pytest.fixture
def make_appointment(app, client):
    """
    Create an appointment in the clinic owning the given headers.

    With no time given, books a free slot a few days ahead. A time in the
    past, or a status of completed / no-show / cancelled, is test state
    the booking rules forbid creating directly, so the appointment is
    booked in the future through the API and then moved into that state
    in the database.
    """

    def _make(session, patient_id, scheduled_at=None, **fields):
        now = datetime.now(timezone.utc)
        slot = next(_appointment_slots)
        if scheduled_at is None:
            scheduled_at = (now + timedelta(days=3, hours=2 * slot)).isoformat()

        target_time = datetime.fromisoformat(scheduled_at)
        target_status = fields.pop("status", None)
        bookable = target_time > now and target_status in (None, "scheduled", "confirmed")

        response = client.post(
            "/api/v1/appointments",
            headers=session["headers"],
            json={
                "patient_id": patient_id,
                "scheduled_at": (
                    scheduled_at if bookable
                    else (now + timedelta(days=400, hours=slot)).isoformat()
                ),
                **({"status": target_status} if bookable and target_status else {}),
                **fields,
            },
        )
        assert response.status_code == 201, response.get_json()
        appointment = response.get_json()["data"]

        if not bookable:
            values = {"scheduled_at": target_time}
            if target_status:
                values["status"] = AppointmentStatus(target_status)
            _direct_update(app, Appointment, appointment["id"], **values)
            appointment = client.get(
                f"/api/v1/appointments/{appointment['id']}", headers=session["headers"]
            ).get_json()["data"]

        return appointment

    return _make


@pytest.fixture
def make_follow_up(app, client):
    """
    Create a follow-up in the clinic owning the given headers.

    A past date (an already-overdue follow-up) cannot be created through
    the API, so it is created for today and then backdated directly.
    """

    def _make(session, patient_id, follow_up_date, reason="Review results", **fields):
        target = date.fromisoformat(follow_up_date)
        in_past = target < date.today()

        response = client.post(
            "/api/v1/follow-ups",
            headers=session["headers"],
            json={
                "patient_id": patient_id,
                "follow_up_date": date.today().isoformat() if in_past else follow_up_date,
                "reason": reason,
                **fields,
            },
        )
        assert response.status_code == 201, response.get_json()
        follow_up = response.get_json()["data"]

        if in_past:
            _direct_update(app, FollowUp, follow_up["id"], follow_up_date=target)
            # There is no single-follow-up endpoint; read it back via the patient.
            listed = client.get(
                f"/api/v1/patients/{patient_id}/follow-ups", headers=session["headers"]
            ).get_json()["data"]
            follow_up = next(f for f in listed if f["id"] == follow_up["id"])

        return follow_up

    return _make


@pytest.fixture
def days_from_today():
    """ISO date N days from today — keeps tests independent of the calendar."""
    from datetime import date, timedelta

    def _offset(days: int) -> str:
        return (date.today() + timedelta(days=days)).isoformat()

    return _offset

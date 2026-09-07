"""
Shared pytest fixtures.

Every test runs against clinicflow_test, created and dropped per
session. Nothing here can touch the development database.
"""

import pytest

from app import create_app
from app.extensions import db as _db


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

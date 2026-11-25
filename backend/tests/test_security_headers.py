"""
Every API response carries the security headers, whatever its outcome.

The point of these headers is that patient data is never cached and never
rendered as a page. An error, a 404 or a refused request can still carry
data or be opened directly, so the tests check every kind of response,
not just the happy path.
"""

import pytest

from app.utils.security_headers import SECURITY_HEADERS


def _assert_secure(response):
    for name, value in SECURITY_HEADERS.items():
        assert response.headers.get(name) == value, (
            f"{response.request.path} -> {response.status_code}: "
            f"{name} was {response.headers.get(name)!r}"
        )


def test_successful_patient_data_is_never_cached(client, register_clinic, make_patient):
    session = register_clinic()
    make_patient(session)

    response = client.get("/api/v1/patients", headers=session["headers"])

    assert response.status_code == 200
    _assert_secure(response)
    assert response.headers["Cache-Control"] == "no-store"


def test_health_check(client):
    _assert_secure(client.get("/api/v1/health"))


@pytest.mark.parametrize(
    "method, path, kwargs, expected_status",
    [
        ("get", "/api/v1/patients", {}, 401),  # no token
        ("get", "/api/v1/does-not-exist", {}, 404),
        ("post", "/api/v1/auth/login", {"json": {"email": "nobody@clinic.test", "password": "wrong-password"}}, 401),
        ("post", "/api/v1/auth/register", {"json": {}}, 422),
    ],
)
def test_error_responses_carry_the_headers_too(client, method, path, kwargs, expected_status):
    response = getattr(client, method)(path, **kwargs)

    assert response.status_code == expected_status
    _assert_secure(response)


def test_scoped_404_for_another_clinics_record(client, register_clinic):
    session = register_clinic()

    response = client.get("/api/v1/patients/999999", headers=session["headers"])

    assert response.status_code == 404
    _assert_secure(response)


def test_cors_preflight(client):
    response = client.options(
        "/api/v1/patients",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    _assert_secure(response)


def test_responses_cannot_be_framed_or_run_anything():
    """Pins the policy itself, so a later edit can't quietly weaken it."""
    csp = SECURITY_HEADERS["Content-Security-Policy"]

    assert "default-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp
    assert SECURITY_HEADERS["X-Frame-Options"] == "DENY"

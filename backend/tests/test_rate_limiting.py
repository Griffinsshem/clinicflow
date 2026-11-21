"""
Rate limiting: who a request is attributed to, and whether limits bite.

All traffic reaches the API through the Next.js server, so without the
trusted client-IP header every visitor would share Vercel's addresses and
one person could exhaust a limit for everybody. These tests pin down both
halves: the real visitor is used when, and only when, the proxy secret
is present; and a forged header without the secret changes nothing.
"""

import pytest

from app import create_app
from app.config import ProductionConfig, TestingConfig
from app.extensions import limiter
from app.utils.client_ip import (
    CLIENT_IP_HEADER,
    PROXY_SECRET_HEADER,
    client_ip,
    login_email_key,
)

SECRET = "test-proxy-secret-0123456789abcdefghijklmnop"
DIRECT_ADDR = "203.0.113.250"  # what Flask sees: the Vercel server


@pytest.fixture
def proxy_secret(app):
    previous = app.config.get("PROXY_SHARED_SECRET")
    app.config["PROXY_SHARED_SECRET"] = SECRET
    yield SECRET
    app.config["PROXY_SHARED_SECRET"] = previous


@pytest.fixture
def limited_client(app, monkeypatch):
    """
    A client for an app with rate limiting switched on.

    The shared testing config disables limits so other tests can register
    clinics freely, and Flask-Limiter only sets up its storage when limits
    are enabled at init. So this builds its own app against the same test
    database, and switches limiting back off afterwards so no other test
    is affected by the shared limiter instance.
    """
    monkeypatch.setattr(TestingConfig, "RATELIMIT_ENABLED", True)
    limited_app = create_app("testing")
    limited_app.config["PROXY_SHARED_SECRET"] = SECRET
    limiter.reset()

    yield limited_app.test_client()

    limiter.reset()
    limiter.enabled = False


def _register(client, email, password="correct-horse-battery"):
    response = client.post(
        "/api/v1/auth/register",
        headers=_from("192.0.2.1"),
        json={
            "clinic_name": "Rate Limit Clinic",
            "full_name": "Test Admin",
            "email": email,
            "password": password,
        },
    )
    assert response.status_code == 201, response.get_json()


def _resolve(app, headers):
    with app.test_request_context(
        "/", headers=headers, environ_base={"REMOTE_ADDR": DIRECT_ADDR}
    ):
        return client_ip()


def _from(ip, secret=SECRET):
    headers = {CLIENT_IP_HEADER: ip}
    if secret is not None:
        headers[PROXY_SECRET_HEADER] = secret
    return headers


class TestClientIpResolution:
    def test_uses_forwarded_ip_with_valid_secret(self, app, proxy_secret):
        assert _resolve(app, _from("198.51.100.7")) == "198.51.100.7"

    def test_accepts_ipv6(self, app, proxy_secret):
        assert _resolve(app, _from("2001:db8::1")) == "2001:db8::1"

    def test_ignores_forwarded_ip_without_secret(self, app, proxy_secret):
        assert _resolve(app, _from("198.51.100.7", secret=None)) == DIRECT_ADDR

    def test_ignores_forwarded_ip_with_wrong_secret(self, app, proxy_secret):
        assert _resolve(app, _from("198.51.100.7", secret="guess")) == DIRECT_ADDR

    def test_non_ascii_secret_does_not_crash(self, app, proxy_secret):
        assert _resolve(app, _from("198.51.100.7", secret="sécret")) == DIRECT_ADDR

    def test_ignores_malformed_ip(self, app, proxy_secret):
        assert _resolve(app, _from("not-an-ip")) == DIRECT_ADDR
        assert _resolve(app, _from("1.2.3.4, 5.6.7.8")) == DIRECT_ADDR

    def test_header_is_never_trusted_when_no_secret_is_configured(self, app):
        app.config["PROXY_SHARED_SECRET"] = ""
        assert _resolve(app, _from("198.51.100.7", secret="")) == DIRECT_ADDR


class TestLoginEmailKey:
    def test_normalises_case_and_whitespace(self, app):
        keys = set()
        for email in ["Ada@Clinic.test", "  ada@clinic.test "]:
            with app.test_request_context(
                "/", method="POST", json={"email": email, "password": "x"}
            ):
                keys.add(login_email_key())
        assert keys == {"login-email:ada@clinic.test"}

    def test_falls_back_to_client_when_email_missing(self, app):
        with app.test_request_context(
            "/", method="POST", data="garbage",
            environ_base={"REMOTE_ADDR": DIRECT_ADDR},
        ):
            assert login_email_key() == f"login-email-missing:{DIRECT_ADDR}"


class TestLimitsApplyPerVisitor:
    def test_one_visitor_exhausting_demo_limit_does_not_block_another(
        self, limited_client
    ):
        client = limited_client
        """The original bug: all visitors shared Vercel's IP and one bucket."""
        for _ in range(3):
            assert client.post("/api/v1/demo", headers=_from("198.51.100.1")).status_code == 201

        assert client.post("/api/v1/demo", headers=_from("198.51.100.1")).status_code == 429
        assert client.post("/api/v1/demo", headers=_from("198.51.100.2")).status_code == 201

    def test_forged_header_cannot_escape_the_limit(self, limited_client):
        """Without the secret, a fresh X-Client-IP per request changes nothing."""
        client = limited_client
        statuses = [
            client.post(
                "/api/v1/demo", headers=_from(f"198.51.100.{i}", secret=None)
            ).status_code
            for i in range(10, 14)
        ]
        assert statuses == [201, 201, 201, 429]

    def test_failed_logins_to_one_account_are_capped_across_ips(
        self, limited_client
    ):
        client = limited_client
        _register(client, "target@clinic.test")

        def attempt(i):
            return client.post(
                "/api/v1/auth/login",
                headers=_from(f"198.51.100.{100 + i}"),
                json={"email": "target@clinic.test", "password": f"wrong-{i}"},
            ).status_code

        # Every attempt from a different IP, so only the per-account limit applies.
        assert [attempt(i) for i in range(10)] == [401] * 10
        assert attempt(10) == 429

    def test_successful_logins_do_not_use_up_the_account_limit(
        self, limited_client
    ):
        client = limited_client
        _register(client, "busy@clinic.test")

        for i in range(12):
            response = client.post(
                "/api/v1/auth/login",
                headers=_from(f"198.51.100.{150 + i}"),
                json={"email": "busy@clinic.test", "password": "correct-horse-battery"},
            )
            assert response.status_code == 200, (i, response.get_json())


class TestProductionRequiresTheSecret:
    def _validate(self, monkeypatch, **overrides):
        values = {
            "SECRET_KEY": "s" * 64,
            "JWT_SECRET_KEY": "j" * 64,
            "SQLALCHEMY_DATABASE_URI": "postgresql+psycopg://u:p@h/db",
            "CORS_ORIGINS": ["https://clinicflow.example"],
            "PROXY_SHARED_SECRET": "p" * 64,
        }
        values.update(overrides)
        for name, value in values.items():
            monkeypatch.setattr(ProductionConfig, name, value)
        ProductionConfig.validate()

    def test_valid_configuration_boots(self, monkeypatch):
        self._validate(monkeypatch)

    @pytest.mark.parametrize("value", ["", "change-me", "short-secret"])
    def test_refuses_to_start_with_weak_secret(self, monkeypatch, value):
        with pytest.raises(RuntimeError, match="PROXY_SHARED_SECRET"):
            self._validate(monkeypatch, PROXY_SHARED_SECRET=value)

    def test_refuses_to_reuse_another_secret(self, monkeypatch):
        with pytest.raises(RuntimeError, match="must differ"):
            self._validate(
                monkeypatch, SECRET_KEY="x" * 64, PROXY_SHARED_SECRET="x" * 64
            )

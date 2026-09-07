"""
Authentication tests.

Focus is on the security properties, not just the happy path: what the
API refuses, what it never leaks, and what it assigns rather than
accepts from the client.
"""

from datetime import timedelta

import pytest
from flask_jwt_extended import create_access_token

from app.models.user import User


class TestRegistration:
    def test_creates_clinic_and_admin(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "clinic_name": "Riverside Clinic",
                "full_name": "Ada Mwangi",
                "email": "ada@riverside.test",
                "password": "correct-horse-battery",
            },
        )
        assert response.status_code == 201
        data = response.get_json()["data"]
        assert data["user"]["role"] == "admin"
        assert data["clinic"]["name"] == "Riverside Clinic"
        assert data["user"]["clinic_id"] == data["clinic"]["id"]

    def test_never_returns_password_hash(self, client):
        body = client.post(
            "/api/v1/auth/register",
            json={
                "clinic_name": "B Clinic",
                "full_name": "B Admin",
                "email": "b@example.test",
                "password": "correct-horse-battery",
            },
        ).get_data(as_text=True)
        assert "password" not in body.lower()

    def test_stores_password_hashed(self, app, client, register_clinic):
        register_clinic(email="hash@example.test", password="correct-horse-battery")
        with app.app_context():
            user = User.query.filter_by(email="hash@example.test").one()
            assert user.password_hash != "correct-horse-battery"
            assert user.password_hash.startswith("scrypt:")
            assert user.check_password("correct-horse-battery")

    def test_rejects_duplicate_email_case_insensitively(self, client, register_clinic):
        register_clinic(email="dupe@example.test")
        response = client.post(
            "/api/v1/auth/register",
            json={
                "clinic_name": "Other Clinic",
                "full_name": "Other Admin",
                "email": "DUPE@example.test",
                "password": "correct-horse-battery",
            },
        )
        assert response.status_code == 409

    @pytest.mark.parametrize(
        "payload,bad_field",
        [
            ({"email": "not-an-email"}, "email"),
            ({"password": "short"}, "password"),
            ({"clinic_name": ""}, "clinic_name"),
        ],
    )
    def test_rejects_invalid_input(self, client, payload, bad_field):
        base = {
            "clinic_name": "Valid Clinic",
            "full_name": "Valid Admin",
            "email": "valid@example.test",
            "password": "correct-horse-battery",
        }
        response = client.post("/api/v1/auth/register", json={**base, **payload})
        assert response.status_code == 422
        assert bad_field in response.get_json()["errors"]

    def test_ignores_client_supplied_role_and_clinic_id(self, client):
        """extra='forbid' must reject privilege-escalation attempts."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "clinic_name": "Sneaky Clinic",
                "full_name": "Sneaky Admin",
                "email": "sneaky@example.test",
                "password": "correct-horse-battery",
                "role": "admin",
                "clinic_id": 1,
            },
        )
        assert response.status_code == 422


class TestLogin:
    def test_succeeds_with_correct_credentials(self, client, register_clinic):
        register_clinic(email="login@example.test", password="correct-horse-battery")
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.test", "password": "correct-horse-battery"},
        )
        assert response.status_code == 200
        assert response.get_json()["data"]["access_token"]

    def test_wrong_password_and_unknown_email_are_indistinguishable(
        self, client, register_clinic
    ):
        """
        Both failures must return an identical body and status, or the
        endpoint becomes an account enumeration oracle.
        """
        register_clinic(email="real@example.test", password="correct-horse-battery")

        wrong_password = client.post(
            "/api/v1/auth/login",
            json={"email": "real@example.test", "password": "wrong-password-here"},
        )
        unknown_email = client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@example.test", "password": "wrong-password-here"},
        )

        assert wrong_password.status_code == unknown_email.status_code == 401
        assert wrong_password.get_json() == unknown_email.get_json()

    def test_email_is_case_insensitive(self, client, register_clinic):
        register_clinic(email="case@example.test", password="correct-horse-battery")
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "CASE@Example.Test", "password": "correct-horse-battery"},
        )
        assert response.status_code == 200


class TestProtectedRoutes:
    def test_requires_a_token(self, client):
        assert client.get("/api/v1/auth/me").status_code == 401

    def test_rejects_a_garbage_token(self, client):
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer not.a.jwt"}
        )
        assert response.status_code == 401

    def test_rejects_an_expired_token(self, app, client, register_clinic):
        session = register_clinic()
        with app.app_context():
            expired = create_access_token(
                identity=str(session["user_id"]), expires_delta=timedelta(seconds=-1)
            )
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"}
        )
        assert response.status_code == 401
        assert "expired" in response.get_json()["message"].lower()

    def test_rejects_token_for_deleted_user(self, app, client, register_clinic):
        """
        A cryptographically valid token for a deleted account must fail.
        This is why auth_required re-loads the user instead of trusting
        the token's claims.
        """
        session = register_clinic()
        with app.app_context():
            from app.extensions import db

            db.session.delete(db.session.get(User, session["user_id"]))
            db.session.commit()

        assert client.get("/api/v1/auth/me", headers=session["headers"]).status_code == 401

    def test_me_returns_user_and_clinic(self, client, register_clinic):
        session = register_clinic()
        response = client.get("/api/v1/auth/me", headers=session["headers"])
        assert response.status_code == 200
        data = response.get_json()["data"]
        assert data["user"]["id"] == session["user_id"]
        assert data["clinic"]["id"] == session["clinic_id"]
        assert "password_hash" not in data["user"]

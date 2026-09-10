"""
Demo provisioning.

The security question here is whether a convenience endpoint has opened
a hole in the isolation model. It has not: demo clinics are ordinary
clinics, and these tests assert that rather than assume it.
"""

from app.models.clinic import Clinic
from app.models.follow_up import FollowUp
from app.models.patient import Patient


class TestDemoProvisioning:
    def test_creates_a_populated_clinic(self, client):
        response = client.post("/api/v1/demo?tz_offset=180")
        assert response.status_code == 201

        data = response.get_json()["data"]
        headers = {"Authorization": f"Bearer {data['access_token']}"}

        patients = client.get("/api/v1/patients", headers=headers).get_json()
        assert patients["meta"]["total"] > 0

        # Every follow-up section should have content, or the demo shows
        # an empty page for the product's most important feature.
        groups = client.get(
            "/api/v1/follow-ups?grouped=true&tz_offset=180", headers=headers
        ).get_json()["data"]
        assert groups["overdue"], "demo must show overdue follow-ups"
        assert groups["due_today"], "demo must show follow-ups due today"
        assert groups["upcoming"], "demo must show upcoming follow-ups"

    def test_each_call_creates_a_separate_clinic(self, app, client):
        first = client.post("/api/v1/demo").get_json()["data"]
        second = client.post("/api/v1/demo").get_json()["data"]

        assert first["clinic"]["id"] != second["clinic"]["id"]
        with app.app_context():
            assert Clinic.query.count() == 2

    def test_demo_clinics_are_isolated_from_each_other(self, client):
        """
        The convenience endpoint must not weaken clinic isolation. Two
        demo visitors are two tenants, with the same guarantees as any
        other pair.
        """
        first = client.post("/api/v1/demo").get_json()["data"]
        second = client.post("/api/v1/demo").get_json()["data"]

        first_headers = {"Authorization": f"Bearer {first['access_token']}"}
        second_headers = {"Authorization": f"Bearer {second['access_token']}"}

        victim = client.get("/api/v1/patients", headers=second_headers).get_json()[
            "data"
        ][0]

        assert (
            client.get(
                f"/api/v1/patients/{victim['id']}", headers=first_headers
            ).status_code
            == 404
        )

    def test_password_is_not_returned(self, client):
        body = client.post("/api/v1/demo").get_data(as_text=True)
        assert "password" not in body.lower()

    def test_returns_404_when_disabled(self, app, client):
        app.config["DEMO_ENABLED"] = False
        try:
            assert client.post("/api/v1/demo").status_code == 404
        finally:
            app.config["DEMO_ENABLED"] = True

    def test_seeded_data_is_consistent(self, app, client):
        """Every seeded row must belong to the clinic that owns it."""
        data = client.post("/api/v1/demo").get_json()["data"]
        clinic_id = data["clinic"]["id"]

        with app.app_context():
            assert all(p.clinic_id == clinic_id for p in Patient.query.all())
            assert all(f.clinic_id == clinic_id for f in FollowUp.query.all())

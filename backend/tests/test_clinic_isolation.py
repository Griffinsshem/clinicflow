"""
Cross-clinic isolation.

The critical requirement: a user from Clinic A must never retrieve or
modify data belonging to Clinic B. These tests exercise that through the
HTTP API, the same path a real attacker would use — not through the
service layer, where a helper could be bypassed.

Every cross-clinic attempt must return 404, not 403. A 403 confirms the
record exists and lets an attacker map the ID space by probing.
"""


class TestPatientIsolation:
    def test_list_shows_only_own_clinic_patients(
        self, client, two_clinics, make_patient
    ):
        make_patient(two_clinics["a"], full_name="Alice OfClinicA")
        make_patient(two_clinics["b"], full_name="Bob OfClinicB")

        response = client.get("/api/v1/patients", headers=two_clinics["a"]["headers"])
        names = [p["full_name"] for p in response.get_json()["data"]]

        assert names == ["Alice OfClinicA"]
        assert response.get_json()["meta"]["total"] == 1

    def test_cannot_read_other_clinic_patient(self, client, two_clinics, make_patient):
        victim = make_patient(two_clinics["b"], full_name="Bob OfClinicB")

        response = client.get(
            f"/api/v1/patients/{victim['id']}", headers=two_clinics["a"]["headers"]
        )
        assert response.status_code == 404
        assert "Bob" not in response.get_data(as_text=True)

    def test_cannot_update_other_clinic_patient(self, client, two_clinics, make_patient):
        victim = make_patient(two_clinics["b"], full_name="Bob OfClinicB")

        response = client.patch(
            f"/api/v1/patients/{victim['id']}",
            headers=two_clinics["a"]["headers"],
            json={"full_name": "Hacked"},
        )
        assert response.status_code == 404

        check = client.get(
            f"/api/v1/patients/{victim['id']}", headers=two_clinics["b"]["headers"]
        )
        assert check.get_json()["data"]["full_name"] == "Bob OfClinicB"

    def test_cannot_delete_other_clinic_patient(self, client, two_clinics, make_patient):
        victim = make_patient(two_clinics["b"], full_name="Bob OfClinicB")

        response = client.delete(
            f"/api/v1/patients/{victim['id']}", headers=two_clinics["a"]["headers"]
        )
        assert response.status_code == 404

        check = client.get(
            f"/api/v1/patients/{victim['id']}", headers=two_clinics["b"]["headers"]
        )
        assert check.status_code == 200

    def test_search_does_not_leak_across_clinics(
        self, client, two_clinics, make_patient
    ):
        make_patient(two_clinics["b"], full_name="Findable Person")

        response = client.get(
            "/api/v1/patients?search=Findable", headers=two_clinics["a"]["headers"]
        )
        assert response.get_json()["data"] == []

    def test_cannot_assign_patient_to_another_clinic(self, client, two_clinics):
        """
        clinic_id is not an accepted field. extra='forbid' makes the
        attempt a visible 422 rather than a silently ignored value.
        """
        response = client.post(
            "/api/v1/patients",
            headers=two_clinics["a"]["headers"],
            json={"full_name": "Smuggled", "clinic_id": two_clinics["b"]["clinic_id"]},
        )
        assert response.status_code == 422
        assert "clinic_id" in response.get_json()["errors"]


class TestPatientRoutesRequireAuth:
    def test_all_patient_routes_reject_anonymous_requests(self, client):
        assert client.get("/api/v1/patients").status_code == 401
        assert client.post("/api/v1/patients", json={"full_name": "X"}).status_code == 401
        assert client.get("/api/v1/patients/1").status_code == 401
        assert client.patch("/api/v1/patients/1", json={"full_name": "X"}).status_code == 401
        assert client.delete("/api/v1/patients/1").status_code == 401


class TestAppointmentIsolation:
    def test_cannot_book_another_clinics_patient(
        self, client, two_clinics, make_patient
    ):
        """
        The composite FK would also reject this, but as a 500. Verifying
        the patient through the scoped helper first makes it a clean 404
        that reveals nothing about the ID.
        """
        victim = make_patient(two_clinics["b"], full_name="Bob OfClinicB")

        response = client.post(
            "/api/v1/appointments",
            headers=two_clinics["a"]["headers"],
            json={
                "patient_id": victim["id"],
                "scheduled_at": "2026-12-01T10:00:00+03:00",
            },
        )
        assert response.status_code == 404

    def test_list_shows_only_own_clinic_appointments(
        self, client, two_clinics, make_patient, make_appointment
    ):
        patient_a = make_patient(two_clinics["a"], full_name="Alice OfClinicA")
        patient_b = make_patient(two_clinics["b"], full_name="Bob OfClinicB")
        make_appointment(two_clinics["a"], patient_a["id"])
        make_appointment(two_clinics["b"], patient_b["id"])

        response = client.get(
            "/api/v1/appointments", headers=two_clinics["a"]["headers"]
        )
        data = response.get_json()["data"]
        assert len(data) == 1
        assert data[0]["patient"]["full_name"] == "Alice OfClinicA"

    def test_cannot_read_update_or_delete_other_clinic_appointment(
        self, client, two_clinics, make_patient, make_appointment
    ):
        patient_b = make_patient(two_clinics["b"])
        appointment = make_appointment(two_clinics["b"], patient_b["id"])
        headers = two_clinics["a"]["headers"]
        url = f"/api/v1/appointments/{appointment['id']}"

        assert client.get(url, headers=headers).status_code == 404
        assert client.patch(url, headers=headers, json={"status": "cancelled"}).status_code == 404
        assert client.delete(url, headers=headers).status_code == 404

        # Untouched from its owner's perspective.
        owner_view = client.get(url, headers=two_clinics["b"]["headers"])
        assert owner_view.get_json()["data"]["status"] == "scheduled"

    def test_cannot_list_another_clinics_patient_history(
        self, client, two_clinics, make_patient
    ):
        victim = make_patient(two_clinics["b"])
        response = client.get(
            f"/api/v1/patients/{victim['id']}/appointments",
            headers=two_clinics["a"]["headers"],
        )
        assert response.status_code == 404


class TestFollowUpIsolation:
    def test_cannot_create_follow_up_for_another_clinics_patient(
        self, client, two_clinics, make_patient, days_from_today
    ):
        victim = make_patient(two_clinics["b"])
        response = client.post(
            "/api/v1/follow-ups",
            headers=two_clinics["a"]["headers"],
            json={
                "patient_id": victim["id"],
                "follow_up_date": days_from_today(7),
                "reason": "Should not work",
            },
        )
        assert response.status_code == 404

    def test_cannot_link_another_clinics_appointment(
        self, client, two_clinics, make_patient, make_appointment, days_from_today
    ):
        """Own patient, but an appointment belonging to another clinic."""
        own = make_patient(two_clinics["a"])
        foreign_patient = make_patient(two_clinics["b"])
        foreign_appointment = make_appointment(two_clinics["b"], foreign_patient["id"])

        response = client.post(
            "/api/v1/follow-ups",
            headers=two_clinics["a"]["headers"],
            json={
                "patient_id": own["id"],
                "appointment_id": foreign_appointment["id"],
                "follow_up_date": days_from_today(7),
                "reason": "Should not work",
            },
        )
        assert response.status_code == 404

    def test_grouped_view_shows_only_own_clinic(
        self, client, two_clinics, make_patient, make_follow_up, days_from_today
    ):
        patient_a = make_patient(two_clinics["a"])
        patient_b = make_patient(two_clinics["b"])
        make_follow_up(two_clinics["a"], patient_a["id"], days_from_today(0), reason="Mine")
        make_follow_up(two_clinics["b"], patient_b["id"], days_from_today(0), reason="Theirs")

        groups = client.get(
            "/api/v1/follow-ups?grouped=true", headers=two_clinics["a"]["headers"]
        ).get_json()["data"]

        assert [f["reason"] for f in groups["due_today"]] == ["Mine"]

    def test_cannot_complete_another_clinics_follow_up(
        self, client, two_clinics, make_patient, make_follow_up, days_from_today
    ):
        patient_b = make_patient(two_clinics["b"])
        follow_up = make_follow_up(two_clinics["b"], patient_b["id"], days_from_today(0))

        response = client.post(
            f"/api/v1/follow-ups/{follow_up['id']}/complete",
            headers=two_clinics["a"]["headers"],
        )
        assert response.status_code == 404

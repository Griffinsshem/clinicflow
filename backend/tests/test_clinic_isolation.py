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

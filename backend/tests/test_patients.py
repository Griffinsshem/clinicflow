import pytest


class TestPatientCrud:
    def test_creates_patient_in_own_clinic(self, client, register_clinic):
        session = register_clinic()
        response = client.post(
            "/api/v1/patients",
            headers=session["headers"],
            json={
                "full_name": "Grace Wanjiru",
                "date_of_birth": "1990-04-12",
                "gender": "female",
                "phone": "+254700000000",
                "email": "grace@example.test",
            },
        )
        assert response.status_code == 201
        data = response.get_json()["data"]
        assert data["clinic_id"] == session["clinic_id"]
        assert data["gender"] == "female"

    def test_optional_fields_may_be_omitted(self, client, register_clinic):
        session = register_clinic()
        response = client.post(
            "/api/v1/patients",
            headers=session["headers"],
            json={"full_name": "Minimal Patient"},
        )
        assert response.status_code == 201
        assert response.get_json()["data"]["phone"] is None

    def test_empty_strings_become_null(self, client, register_clinic):
        """HTML forms send "" for untouched inputs; we store NULL."""
        session = register_clinic()
        response = client.post(
            "/api/v1/patients",
            headers=session["headers"],
            json={"full_name": "Blank Fields", "phone": "", "email": ""},
        )
        assert response.status_code == 201
        assert response.get_json()["data"]["phone"] is None
        assert response.get_json()["data"]["email"] is None

    def test_updates_only_supplied_fields(self, client, register_clinic, make_patient):
        session = register_clinic()
        patient = make_patient(session, full_name="Before", phone="+254711111111")

        response = client.patch(
            f"/api/v1/patients/{patient['id']}",
            headers=session["headers"],
            json={"full_name": "After"},
        )
        assert response.status_code == 200
        data = response.get_json()["data"]
        assert data["full_name"] == "After"
        assert data["phone"] == "+254711111111"  

    def test_rejects_empty_patch(self, client, register_clinic, make_patient):
        session = register_clinic()
        patient = make_patient(session)
        response = client.patch(
            f"/api/v1/patients/{patient['id']}", headers=session["headers"], json={}
        )
        assert response.status_code == 422

    def test_deletes_patient(self, client, register_clinic, make_patient):
        session = register_clinic()
        patient = make_patient(session)

        assert client.delete(
            f"/api/v1/patients/{patient['id']}", headers=session["headers"]
        ).status_code == 200
        assert client.get(
            f"/api/v1/patients/{patient['id']}", headers=session["headers"]
        ).status_code == 404

    def test_missing_patient_returns_404(self, client, register_clinic):
        session = register_clinic()
        assert client.get(
            "/api/v1/patients/999999", headers=session["headers"]
        ).status_code == 404


class TestPatientValidation:
    @pytest.mark.parametrize(
        "payload,bad_field",
        [
            ({"full_name": ""}, "full_name"),
            ({"full_name": "A"}, "full_name"),
            ({"full_name": "Ok", "gender": "banana"}, "gender"),
            ({"full_name": "Ok", "date_of_birth": "not-a-date"}, "date_of_birth"),
            ({"full_name": "Ok", "date_of_birth": "2999-01-01"}, "date_of_birth"),
            ({"full_name": "Ok", "email": "nope"}, "email"),
        ],
    )
    def test_rejects_invalid_input(self, client, register_clinic, payload, bad_field):
        session = register_clinic()
        response = client.post(
            "/api/v1/patients", headers=session["headers"], json=payload
        )
        assert response.status_code == 422
        assert bad_field in response.get_json()["errors"]


class TestPatientSearchAndPagination:
    def test_search_matches_name_and_phone(self, client, register_clinic, make_patient):
        session = register_clinic()
        make_patient(session, full_name="Alice Kimani", phone="+254700111222")
        make_patient(session, full_name="Bob Otieno", phone="+254733444555")

        by_name = client.get("/api/v1/patients?search=alice", headers=session["headers"])
        assert len(by_name.get_json()["data"]) == 1

        by_phone = client.get(
            "/api/v1/patients?search=733444", headers=session["headers"]
        )
        assert by_phone.get_json()["data"][0]["full_name"] == "Bob Otieno"

    def test_wildcards_in_search_are_literal(self, client, register_clinic, make_patient):
        """
        An unescaped % would match every row. Escaping means the search
        finds only the patient whose name actually contains it.
        """
        session = register_clinic()
        make_patient(session, full_name="Normal Patient")
        make_patient(session, full_name="Odd %Name")

        response = client.get("/api/v1/patients?search=%25", headers=session["headers"])
        names = [p["full_name"] for p in response.get_json()["data"]]
        assert names == ["Odd %Name"]

    def test_limit_is_capped(self, client, register_clinic):
        """A client cannot request unbounded rows."""
        session = register_clinic()
        response = client.get(
            "/api/v1/patients?limit=999999", headers=session["headers"]
        )
        assert response.get_json()["meta"]["limit"] == 100

    def test_pagination_metadata(self, client, register_clinic, make_patient):
        session = register_clinic()
        for i in range(5):
            make_patient(session, full_name=f"Patient {i:02d}")

        response = client.get("/api/v1/patients?limit=2&page=2", headers=session["headers"])
        body = response.get_json()
        assert len(body["data"]) == 2
        assert body["meta"] == {"page": 2, "limit": 2, "total": 5, "pages": 3}

    def test_invalid_pagination_falls_back_to_defaults(self, client, register_clinic):
        session = register_clinic()
        response = client.get(
            "/api/v1/patients?page=abc&limit=xyz", headers=session["headers"]
        )
        assert response.get_json()["meta"]["page"] == 1
        assert response.get_json()["meta"]["limit"] == 20

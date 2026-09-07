"""Appointment CRUD, validation, status transitions, and filtering."""

import pytest


class TestAppointmentCrud:
    def test_schedules_an_appointment(self, client, register_clinic, make_patient):
        session = register_clinic()
        patient = make_patient(session)

        response = client.post(
            "/api/v1/appointments",
            headers=session["headers"],
            json={
                "patient_id": patient["id"],
                "scheduled_at": "2026-12-01T10:00:00+03:00",
                "appointment_type": "consultation",
                "notes": "Initial visit",
            },
        )
        assert response.status_code == 201
        data = response.get_json()["data"]
        assert data["status"] == "scheduled"
        assert data["patient"]["full_name"] == patient["full_name"]

    def test_defaults_type_and_status(self, client, register_clinic, make_patient):
        session = register_clinic()
        patient = make_patient(session)
        appointment = client.post(
            "/api/v1/appointments",
            headers=session["headers"],
            json={"patient_id": patient["id"], "scheduled_at": "2026-12-01T10:00:00+03:00"},
        ).get_json()["data"]

        assert appointment["appointment_type"] == "consultation"
        assert appointment["status"] == "scheduled"

    def test_lists_patient_history(
        self, client, register_clinic, make_patient, make_appointment
    ):
        session = register_clinic()
        patient = make_patient(session)
        make_appointment(session, patient["id"], "2026-11-01T09:00:00+03:00")
        make_appointment(session, patient["id"], "2026-12-01T09:00:00+03:00")

        response = client.get(
            f"/api/v1/patients/{patient['id']}/appointments", headers=session["headers"]
        )
        data = response.get_json()["data"]
        assert len(data) == 2
        # Newest first.
        assert data[0]["scheduled_at"] > data[1]["scheduled_at"]

    def test_deleting_patient_cascades_to_appointments(
        self, client, register_clinic, make_patient, make_appointment
    ):
        session = register_clinic()
        patient = make_patient(session)
        appointment = make_appointment(session, patient["id"])

        client.delete(f"/api/v1/patients/{patient['id']}", headers=session["headers"])

        assert client.get(
            f"/api/v1/appointments/{appointment['id']}", headers=session["headers"]
        ).status_code == 404


class TestAppointmentValidation:
    def test_rejects_naive_datetime(self, client, register_clinic, make_patient):
        """Without an offset, the intended instant is ambiguous."""
        session = register_clinic()
        patient = make_patient(session)

        response = client.post(
            "/api/v1/appointments",
            headers=session["headers"],
            json={"patient_id": patient["id"], "scheduled_at": "2026-12-01T10:00:00"},
        )
        assert response.status_code == 422
        assert "scheduled_at" in response.get_json()["errors"]

    @pytest.mark.parametrize(
        "payload,bad_field",
        [
            ({"appointment_type": "surgery"}, "appointment_type"),
            ({"status": "pending"}, "status"),
            ({"notes": "x" * 1001}, "notes"),
        ],
    )
    def test_rejects_invalid_fields(
        self, client, register_clinic, make_patient, payload, bad_field
    ):
        session = register_clinic()
        patient = make_patient(session)
        response = client.post(
            "/api/v1/appointments",
            headers=session["headers"],
            json={
                "patient_id": patient["id"],
                "scheduled_at": "2026-12-01T10:00:00+03:00",
                **payload,
            },
        )
        assert response.status_code == 422
        assert bad_field in response.get_json()["errors"]

    def test_rejects_nonexistent_patient(self, client, register_clinic):
        session = register_clinic()
        response = client.post(
            "/api/v1/appointments",
            headers=session["headers"],
            json={"patient_id": 999999, "scheduled_at": "2026-12-01T10:00:00+03:00"},
        )
        assert response.status_code == 404

    def test_cannot_reassign_patient(
        self, client, register_clinic, make_patient, make_appointment
    ):
        """patient_id is not updatable — cancel and rebook instead."""
        session = register_clinic()
        patient = make_patient(session)
        other = make_patient(session, full_name="Other Patient")
        appointment = make_appointment(session, patient["id"])

        response = client.patch(
            f"/api/v1/appointments/{appointment['id']}",
            headers=session["headers"],
            json={"patient_id": other["id"]},
        )
        assert response.status_code == 422


class TestStatusTransitions:
    @pytest.mark.parametrize(
        "first,second",
        [("confirmed", "completed"), ("scheduled", "cancelled"), ("no_show", "scheduled")],
    )
    def test_allows_legal_transitions(
        self, client, register_clinic, make_patient, make_appointment, first, second
    ):
        session = register_clinic()
        patient = make_patient(session)
        appointment = make_appointment(session, patient["id"])

        for status in (first, second):
            response = client.patch(
                f"/api/v1/appointments/{appointment['id']}",
                headers=session["headers"],
                json={"status": status},
            )
            assert response.status_code == 200, response.get_json()
        assert response.get_json()["data"]["status"] == second

    @pytest.mark.parametrize(
        "terminal,attempted",
        [("cancelled", "completed"), ("completed", "scheduled"), ("completed", "cancelled")],
    )
    def test_rejects_illegal_transitions(
        self, client, register_clinic, make_patient, make_appointment, terminal, attempted
    ):
        session = register_clinic()
        patient = make_patient(session)
        appointment = make_appointment(session, patient["id"])

        client.patch(
            f"/api/v1/appointments/{appointment['id']}",
            headers=session["headers"],
            json={"status": terminal},
        )
        response = client.patch(
            f"/api/v1/appointments/{appointment['id']}",
            headers=session["headers"],
            json={"status": attempted},
        )
        assert response.status_code == 422
        assert "status" in response.get_json()["errors"]


class TestAppointmentFilters:
    def test_filters_by_status_and_type(
        self, client, register_clinic, make_patient, make_appointment
    ):
        session = register_clinic()
        patient = make_patient(session)
        make_appointment(session, patient["id"], appointment_type="check_up")
        second = make_appointment(session, patient["id"], appointment_type="consultation")
        client.patch(
            f"/api/v1/appointments/{second['id']}",
            headers=session["headers"],
            json={"status": "confirmed"},
        )

        by_status = client.get(
            "/api/v1/appointments?status=confirmed", headers=session["headers"]
        )
        assert len(by_status.get_json()["data"]) == 1

        by_type = client.get(
            "/api/v1/appointments?appointment_type=check_up", headers=session["headers"]
        )
        assert len(by_type.get_json()["data"]) == 1

    def test_filters_by_date_range(
        self, client, register_clinic, make_patient, make_appointment
    ):
        session = register_clinic()
        patient = make_patient(session)
        make_appointment(session, patient["id"], "2026-11-01T09:00:00+03:00")
        make_appointment(session, patient["id"], "2026-12-15T09:00:00+03:00")

        response = client.get(
            "/api/v1/appointments?date_from=2026-12-01T00:00:00%2B03:00",
            headers=session["headers"],
        )
        assert len(response.get_json()["data"]) == 1

    def test_invalid_filter_errors_rather_than_ignoring(self, client, register_clinic):
        """A filter that fails open would silently return everything."""
        session = register_clinic()
        response = client.get(
            "/api/v1/appointments?status=nonsense", headers=session["headers"]
        )
        assert response.status_code == 422
        assert "status" in response.get_json()["errors"]

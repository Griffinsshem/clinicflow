"""Follow-up CRUD, derived overdue status, grouping, and completion."""

import pytest


class TestFollowUpCrud:
    def test_creates_follow_up(
        self, client, register_clinic, make_patient, days_from_today
    ):
        session = register_clinic()
        patient = make_patient(session)

        response = client.post(
            "/api/v1/follow-ups",
            headers=session["headers"],
            json={
                "patient_id": patient["id"],
                "follow_up_date": days_from_today(7),
                "reason": "Review blood test results",
            },
        )
        assert response.status_code == 201
        data = response.get_json()["data"]
        assert data["status"] == "upcoming"
        assert data["is_overdue"] is False

    def test_links_to_originating_appointment(
        self, client, register_clinic, make_patient, make_appointment, days_from_today
    ):
        session = register_clinic()
        patient = make_patient(session)
        appointment = make_appointment(session, patient["id"])

        follow_up = client.post(
            "/api/v1/follow-ups",
            headers=session["headers"],
            json={
                "patient_id": patient["id"],
                "appointment_id": appointment["id"],
                "follow_up_date": days_from_today(14),
                "reason": "Post-visit check",
            },
        ).get_json()["data"]

        assert follow_up["appointment_id"] == appointment["id"]

    def test_deleting_appointment_preserves_follow_up(
        self, client, register_clinic, make_patient, make_appointment, days_from_today
    ):
        """
        ON DELETE SET NULL, not CASCADE: losing the appointment must not
        erase the outstanding commitment to see the patient.
        """
        session = register_clinic()
        patient = make_patient(session)
        appointment = make_appointment(session, patient["id"])
        follow_up = client.post(
            "/api/v1/follow-ups",
            headers=session["headers"],
            json={
                "patient_id": patient["id"],
                "appointment_id": appointment["id"],
                "follow_up_date": days_from_today(7),
                "reason": "Still needed",
            },
        ).get_json()["data"]

        client.delete(
            f"/api/v1/appointments/{appointment['id']}", headers=session["headers"]
        )

        remaining = client.get(
            f"/api/v1/patients/{patient['id']}/follow-ups", headers=session["headers"]
        ).get_json()["data"]

        assert len(remaining) == 1
        assert remaining[0]["id"] == follow_up["id"]
        assert remaining[0]["appointment_id"] is None

    @pytest.mark.parametrize(
        "payload,bad_field",
        [
            ({"reason": ""}, "reason"),
            ({"reason": "ab"}, "reason"),
            ({"follow_up_date": "not-a-date"}, "follow_up_date"),
            ({"status": "overdue"}, "status"),
        ],
    )
    def test_rejects_invalid_input(
        self, client, register_clinic, make_patient, days_from_today, payload, bad_field
    ):
        session = register_clinic()
        patient = make_patient(session)
        response = client.post(
            "/api/v1/follow-ups",
            headers=session["headers"],
            json={
                "patient_id": patient["id"],
                "follow_up_date": days_from_today(7),
                "reason": "Valid reason",
                **payload,
            },
        )
        assert response.status_code == 422


class TestOverdueIsDerived:
    def test_past_date_reports_overdue(
        self, client, register_clinic, make_patient, make_follow_up, days_from_today
    ):
        """
        'overdue' is never written to the database — the stored status
        stays 'upcoming' and the flag is computed on read.
        """
        session = register_clinic()
        patient = make_patient(session)
        follow_up = make_follow_up(session, patient["id"], days_from_today(-3))

        assert follow_up["status"] == "upcoming"
        assert follow_up["is_overdue"] is True

    def test_today_is_due_not_overdue(
        self, client, register_clinic, make_patient, make_follow_up, days_from_today
    ):
        session = register_clinic()
        patient = make_patient(session)
        follow_up = make_follow_up(session, patient["id"], days_from_today(0))

        assert follow_up["is_due_today"] is True
        assert follow_up["is_overdue"] is False

    def test_completed_is_never_overdue(
        self, client, register_clinic, make_patient, make_follow_up, days_from_today
    ):
        session = register_clinic()
        patient = make_patient(session)
        follow_up = make_follow_up(session, patient["id"], days_from_today(-10))

        client.post(
            f"/api/v1/follow-ups/{follow_up['id']}/complete", headers=session["headers"]
        )
        remaining = client.get(
            f"/api/v1/patients/{patient['id']}/follow-ups", headers=session["headers"]
        ).get_json()["data"]

        assert remaining[0]["status"] == "completed"
        assert remaining[0]["is_overdue"] is False

    def test_overdue_filter(
        self, client, register_clinic, make_patient, make_follow_up, days_from_today
    ):
        session = register_clinic()
        patient = make_patient(session)
        make_follow_up(session, patient["id"], days_from_today(-5), reason="Late one")
        make_follow_up(session, patient["id"], days_from_today(5), reason="Future one")

        response = client.get(
            "/api/v1/follow-ups?overdue=true", headers=session["headers"]
        )
        data = response.get_json()["data"]
        assert len(data) == 1
        assert data[0]["reason"] == "Late one"


class TestGroupedView:
    def test_groups_into_ui_sections(
        self, client, register_clinic, make_patient, make_follow_up, days_from_today
    ):
        session = register_clinic()
        patient = make_patient(session)
        make_follow_up(session, patient["id"], days_from_today(-2), reason="Overdue one")
        make_follow_up(session, patient["id"], days_from_today(0), reason="Due today")
        make_follow_up(session, patient["id"], days_from_today(9), reason="Upcoming one")

        groups = client.get(
            "/api/v1/follow-ups?grouped=true", headers=session["headers"]
        ).get_json()["data"]

        assert [f["reason"] for f in groups["overdue"]] == ["Overdue one"]
        assert [f["reason"] for f in groups["due_today"]] == ["Due today"]
        assert [f["reason"] for f in groups["upcoming"]] == ["Upcoming one"]
        assert groups["completed"] == []


class TestCompletionWorkflow:
    def test_completes_and_schedules_next_appointment(
        self, client, register_clinic, make_patient, make_follow_up, days_from_today
    ):
        """The core loop: complete a follow-up, book the next visit, atomically."""
        session = register_clinic()
        patient = make_patient(session)
        follow_up = make_follow_up(session, patient["id"], days_from_today(0))

        response = client.post(
            f"/api/v1/follow-ups/{follow_up['id']}/complete",
            headers=session["headers"],
            json={"scheduled_at": "2027-01-15T09:30:00+03:00", "notes": "Six-week review"},
        )
        assert response.status_code == 200
        data = response.get_json()["data"]

        assert data["follow_up"]["status"] == "completed"
        assert data["appointment"]["patient_id"] == patient["id"]
        assert data["appointment"]["appointment_type"] == "follow_up"

    def test_completes_without_scheduling(
        self, client, register_clinic, make_patient, make_follow_up, days_from_today
    ):
        session = register_clinic()
        patient = make_patient(session)
        follow_up = make_follow_up(session, patient["id"], days_from_today(0))

        response = client.post(
            f"/api/v1/follow-ups/{follow_up['id']}/complete", headers=session["headers"]
        )
        assert response.status_code == 200
        assert response.get_json()["data"]["appointment"] is None

    def test_cannot_complete_twice(
        self, client, register_clinic, make_patient, make_follow_up, days_from_today
    ):
        session = register_clinic()
        patient = make_patient(session)
        follow_up = make_follow_up(session, patient["id"], days_from_today(0))
        url = f"/api/v1/follow-ups/{follow_up['id']}/complete"

        assert client.post(url, headers=session["headers"]).status_code == 200
        assert client.post(url, headers=session["headers"]).status_code == 409

    def test_rejects_naive_datetime_when_scheduling(
        self, client, register_clinic, make_patient, make_follow_up, days_from_today
    ):
        session = register_clinic()
        patient = make_patient(session)
        follow_up = make_follow_up(session, patient["id"], days_from_today(0))

        response = client.post(
            f"/api/v1/follow-ups/{follow_up['id']}/complete",
            headers=session["headers"],
            json={"scheduled_at": "2027-01-15T09:30:00"},
        )
        assert response.status_code == 422

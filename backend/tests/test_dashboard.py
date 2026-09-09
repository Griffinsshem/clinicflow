from datetime import datetime, timedelta, timezone


def _iso_in(hours: float, tz_offset_hours: int = 3) -> str:
    tz = timezone(timedelta(hours=tz_offset_hours))
    return (datetime.now(tz) + timedelta(hours=hours)).isoformat()


def _iso_today_at(hour: int, tz_offset_hours: int = 3) -> str:
    """
    A fixed clock time on today's date in the given zone.

    Offsetting from "now" makes a test time-of-day dependent: run at
    20:30 with a +5h offset and the appointment lands tomorrow, so a
    test asserting "two appointments today" fails for reasons that have
    nothing to do with the code. Pinning the hour keeps the assertion
    about behaviour rather than about when the suite happened to run.
    """
    tz = timezone(timedelta(hours=tz_offset_hours))
    return datetime.now(tz).replace(
        hour=hour, minute=0, second=0, microsecond=0
    ).isoformat()


class TestDashboardMetrics:
    def test_empty_clinic_returns_zeros(self, client, register_clinic):
        """Empty states must render, not error."""
        session = register_clinic()
        data = client.get("/api/v1/dashboard", headers=session["headers"]).get_json()["data"]

        assert data["metrics"]["total_patients"] == 0
        assert data["today_schedule"] == []
        assert data["attention_follow_ups"] == []
        assert len(data["weekly_activity"]) == 7

    def test_counts_patients_and_appointments(
        self, client, register_clinic, make_patient, make_appointment
    ):
        session = register_clinic()
        patient = make_patient(session)
        make_appointment(session, patient["id"], _iso_today_at(11))       
        make_appointment(session, patient["id"], _iso_in(24 * 5))  

        response = client.get(
            "/api/v1/dashboard?tz_offset=180", headers=session["headers"]
        )
        metrics = response.get_json()["data"]["metrics"]

        assert metrics["total_patients"] == 1
        assert metrics["appointments_today"] == 1
        assert metrics["upcoming_appointments"] == 1

    def test_cancelled_appointments_are_excluded(
        self, client, register_clinic, make_patient, make_appointment
    ):
        """A cancelled visit must not inflate the day's workload."""
        session = register_clinic()
        patient = make_patient(session)
        appointment = make_appointment(session, patient["id"], _iso_today_at(11))

        client.patch(
            f"/api/v1/appointments/{appointment['id']}",
            headers=session["headers"],
            json={"status": "cancelled"},
        )

        metrics = client.get(
            "/api/v1/dashboard?tz_offset=180", headers=session["headers"]
        ).get_json()["data"]["metrics"]
        assert metrics["appointments_today"] == 0

    def test_follow_up_attention_counts(
        self, client, register_clinic, make_patient, make_follow_up, days_from_today
    ):
        session = register_clinic()
        patient = make_patient(session)
        make_follow_up(session, patient["id"], days_from_today(-4), reason="Overdue one")
        make_follow_up(session, patient["id"], days_from_today(0), reason="Due today")
        make_follow_up(session, patient["id"], days_from_today(6), reason="Later")

        data = client.get("/api/v1/dashboard", headers=session["headers"]).get_json()["data"]
        metrics = data["metrics"]

        assert metrics["follow_ups_overdue"] == 1
        assert metrics["follow_ups_due_today"] == 1
        assert metrics["follow_ups_needing_attention"] == 2
        assert [f["reason"] for f in data["attention_follow_ups"]] == [
            "Overdue one",
            "Due today",
        ]

    def test_todays_schedule_is_chronological(
        self, client, register_clinic, make_patient, make_appointment
    ):
        session = register_clinic()
        patient = make_patient(session)
        make_appointment(session, patient["id"], _iso_today_at(14))
        make_appointment(session, patient["id"], _iso_today_at(9))

        schedule = client.get(
            "/api/v1/dashboard?tz_offset=180", headers=session["headers"]
        ).get_json()["data"]["today_schedule"]

        assert len(schedule) == 2
        assert schedule[0]["scheduled_at"] < schedule[1]["scheduled_at"]
        assert schedule[0]["patient"]["full_name"] == patient["full_name"]


class TestDashboardTimezone:
    def test_invalid_offset_falls_back_to_utc(self, client, register_clinic):
        """
        tz_offset feeds a Postgres timezone literal, so malformed or
        absurd values must be rejected before reaching SQL — not error,
        and not be interpolated.
        """
        session = register_clinic()
        for bad in ("abc", "99999", "-99999", "", "'; DROP TABLE patients--"):
            response = client.get(
                f"/api/v1/dashboard?tz_offset={bad}", headers=session["headers"]
            )
            assert response.status_code == 200, bad


class TestDashboardIsolation:
    def test_metrics_count_only_own_clinic(
        self, client, two_clinics, make_patient, make_appointment
    ):
        """
        A leaky aggregate discloses another clinic's patient volume even
        without exposing a single record.
        """
        make_patient(two_clinics["a"])
        make_patient(two_clinics["b"])
        make_patient(two_clinics["b"], full_name="Second B Patient")

        metrics = client.get(
            "/api/v1/dashboard", headers=two_clinics["a"]["headers"]
        ).get_json()["data"]["metrics"]

        assert metrics["total_patients"] == 1

    def test_schedule_shows_only_own_clinic(
        self, client, two_clinics, make_patient, make_appointment
    ):
        patient_a = make_patient(two_clinics["a"], full_name="Alice OfClinicA")
        patient_b = make_patient(two_clinics["b"], full_name="Bob OfClinicB")
        make_appointment(two_clinics["a"], patient_a["id"], _iso_today_at(11))
        make_appointment(two_clinics["b"], patient_b["id"], _iso_today_at(11))

        schedule = client.get(
            "/api/v1/dashboard?tz_offset=180", headers=two_clinics["a"]["headers"]
        ).get_json()["data"]["today_schedule"]

        assert len(schedule) == 1
        assert schedule[0]["patient"]["full_name"] == "Alice OfClinicA"

    def test_requires_authentication(self, client):
        assert client.get("/api/v1/dashboard").status_code == 401

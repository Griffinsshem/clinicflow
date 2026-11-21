"""
Data-integrity rules for appointments and follow-ups.

Each class covers one rule. Several reproduce bugs found on the live demo
before these rules existed: a completed visit moved to 2030, a completed
follow-up reopened through PATCH, a follow-up linked to another patient's
appointment, a follow-up dated 2020 and an appointment dated 2001, and
two appointments booked for the same patient at the same moment.
"""

from datetime import date, datetime, timedelta, timezone

import pytest

EAT = timezone(timedelta(hours=3))


def _at(**delta) -> str:
    """An ISO timestamp relative to now, at minute precision, in UTC+3."""
    return (datetime.now(EAT) + timedelta(**delta)).replace(
        second=0, microsecond=0
    ).isoformat()


def _day(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


@pytest.fixture
def clinic(register_clinic, make_patient):
    session = register_clinic()
    return {
        "session": session,
        "headers": session["headers"],
        "patient": make_patient(session),
        "other_patient": make_patient(session, full_name="Other Patient"),
    }


def _book(client, clinic, scheduled_at, patient=None, **fields):
    patient = patient or clinic["patient"]
    return client.post(
        "/api/v1/appointments",
        headers=clinic["headers"],
        json={"patient_id": patient["id"], "scheduled_at": scheduled_at, **fields},
    )


def _patch_appointment(client, clinic, appointment_id, **changes):
    return client.patch(
        f"/api/v1/appointments/{appointment_id}", headers=clinic["headers"], json=changes
    )


def _field_error(response, field):
    return response.get_json().get("errors", {}).get(field)


# --- Rule 1: completed, cancelled and no-show appointments keep their time and type


class TestLockedAppointments:
    @pytest.mark.parametrize("status", ["completed", "cancelled", "no_show"])
    def test_cannot_move_a_finished_appointment(
        self, client, clinic, make_appointment, status
    ):
        """Reproduces the demo bug: a completed visit rescheduled to 2030."""
        appointment = make_appointment(
            clinic["session"], clinic["patient"]["id"], _at(days=-1), status=status
        )

        response = _patch_appointment(
            client, clinic, appointment["id"], scheduled_at=_at(days=30)
        )

        assert response.status_code == 422
        assert _field_error(response, "scheduled_at")

    def test_cannot_change_type_of_completed_appointment(
        self, client, clinic, make_appointment
    ):
        appointment = make_appointment(
            clinic["session"], clinic["patient"]["id"], _at(days=-1), status="completed"
        )

        assert appointment["appointment_type"] == "consultation"

        response = _patch_appointment(
            client, clinic, appointment["id"], appointment_type="check_up"
        )

        assert response.status_code == 422
        assert "no longer change" in _field_error(response, "appointment_type")

    def test_notes_stay_editable_after_completion(
        self, client, clinic, make_appointment
    ):
        """Staff write visit notes after the visit; that must keep working."""
        appointment = make_appointment(
            clinic["session"], clinic["patient"]["id"], _at(days=-1), status="completed"
        )

        response = _patch_appointment(
            client, clinic, appointment["id"], notes="BP 120/80, review in 6 weeks"
        )

        assert response.status_code == 200, response.get_json()
        assert response.get_json()["data"]["notes"] == "BP 120/80, review in 6 weeks"

    def test_edit_form_resending_unchanged_time_and_type_is_accepted(
        self, client, clinic, make_appointment
    ):
        """
        The edit form always sends date, type and notes together, at minute
        precision. Saving only a notes change must not count as moving it.
        """
        appointment = make_appointment(
            clinic["session"], clinic["patient"]["id"], _at(days=-1), status="completed"
        )

        response = _patch_appointment(
            client,
            clinic,
            appointment["id"],
            scheduled_at=appointment["scheduled_at"],
            appointment_type=appointment["appointment_type"],
            notes="Added after the visit",
        )

        assert response.status_code == 200, response.get_json()

    def test_no_show_can_be_rebooked_with_a_new_time(
        self, client, clinic, make_appointment
    ):
        appointment = make_appointment(
            clinic["session"], clinic["patient"]["id"], _at(days=-1), status="no_show"
        )

        response = _patch_appointment(
            client, clinic, appointment["id"], status="scheduled", scheduled_at=_at(days=7)
        )

        assert response.status_code == 200, response.get_json()
        assert response.get_json()["data"]["status"] == "scheduled"


# --- Rule 2: follow-up status changes only through Complete


class TestFollowUpStatusChanges:
    def _follow_up(self, make_follow_up, clinic):
        return make_follow_up(clinic["session"], clinic["patient"]["id"], _day(3))

    def _patch(self, client, clinic, follow_up_id, **changes):
        return client.patch(
            f"/api/v1/follow-ups/{follow_up_id}", headers=clinic["headers"], json=changes
        )

    def test_cannot_complete_through_patch(self, client, clinic, make_follow_up):
        follow_up = self._follow_up(make_follow_up, clinic)

        response = self._patch(client, clinic, follow_up["id"], status="completed")

        assert response.status_code == 422
        assert _field_error(response, "status")

    def test_cannot_reopen_a_completed_follow_up(self, client, clinic, make_follow_up):
        """Reproduces the demo bug: completed set back to upcoming via PATCH."""
        follow_up = self._follow_up(make_follow_up, clinic)
        client.post(
            f"/api/v1/follow-ups/{follow_up['id']}/complete", headers=clinic["headers"]
        )

        response = self._patch(client, clinic, follow_up["id"], status="upcoming")

        assert response.status_code == 422
        assert "reopened" in response.get_json()["message"]

    def test_repeating_the_current_status_is_harmless(
        self, client, clinic, make_follow_up
    ):
        follow_up = self._follow_up(make_follow_up, clinic)

        response = self._patch(
            client, clinic, follow_up["id"], status="upcoming", reason="Check bloods"
        )

        assert response.status_code == 200, response.get_json()
        assert response.get_json()["data"]["reason"] == "Check bloods"

    def test_completed_follow_up_keeps_its_date(self, client, clinic, make_follow_up):
        follow_up = self._follow_up(make_follow_up, clinic)
        client.post(
            f"/api/v1/follow-ups/{follow_up['id']}/complete", headers=clinic["headers"]
        )

        response = self._patch(client, clinic, follow_up["id"], follow_up_date=_day(20))

        assert response.status_code == 422
        assert _field_error(response, "follow_up_date")


# --- Rule 3: a follow-up's appointment belongs to the same patient


class TestFollowUpAppointmentLink:
    def _create(self, client, clinic, patient, appointment_id):
        return client.post(
            "/api/v1/follow-ups",
            headers=clinic["headers"],
            json={
                "patient_id": patient["id"],
                "appointment_id": appointment_id,
                "follow_up_date": _day(7),
                "reason": "Review results",
            },
        )

    def test_rejects_another_patients_appointment(
        self, client, clinic, make_appointment
    ):
        """Reproduces the demo bug: a follow-up linked across patients."""
        appointment = make_appointment(clinic["session"], clinic["patient"]["id"])

        response = self._create(client, clinic, clinic["other_patient"], appointment["id"])

        assert response.status_code == 422
        assert _field_error(response, "appointment_id")

    def test_accepts_the_patients_own_appointment(
        self, client, clinic, make_appointment
    ):
        appointment = make_appointment(clinic["session"], clinic["patient"]["id"])

        response = self._create(client, clinic, clinic["patient"], appointment["id"])

        assert response.status_code == 201, response.get_json()
        assert response.get_json()["data"]["appointment_id"] == appointment["id"]


# --- Rule 4: dates must make sense


class TestAppointmentDates:
    def test_rejects_booking_in_the_past(self, client, clinic):
        """Reproduces the demo bug: an appointment accepted for 2001."""
        response = _book(client, clinic, "2001-01-01T09:00:00+03:00")

        assert response.status_code == 422
        assert _field_error(response, "scheduled_at")

    def test_rejects_yesterday(self, client, clinic):
        response = _book(client, clinic, _at(days=-1))

        assert response.status_code == 422

    def test_allows_a_walk_in_that_started_minutes_ago(self, client, clinic):
        response = _book(client, clinic, _at(minutes=-20))

        assert response.status_code == 201, response.get_json()

    def test_rejects_more_than_two_years_ahead(self, client, clinic):
        """Catches typos like 2062 for 2026."""
        response = _book(client, clinic, _at(days=800))

        assert response.status_code == 422
        assert "two years" in _field_error(response, "scheduled_at")

    def test_can_record_a_past_completed_visit(self, client, clinic):
        """Back-entry of a visit that already happened is legitimate."""
        response = _book(client, clinic, _at(days=-3), status="completed")

        assert response.status_code == 201, response.get_json()

    def test_cannot_record_a_future_visit_as_completed(self, client, clinic):
        response = _book(client, clinic, _at(days=3), status="completed")

        assert response.status_code == 422

    @pytest.mark.parametrize("outcome", ["completed", "no_show"])
    def test_cannot_mark_a_future_visit_as_happened(
        self, client, clinic, make_appointment, outcome
    ):
        appointment = make_appointment(
            clinic["session"], clinic["patient"]["id"], _at(days=2)
        )

        response = _patch_appointment(client, clinic, appointment["id"], status=outcome)

        assert response.status_code == 422
        assert _field_error(response, "status")
        assert "hasn't" in response.get_json()["message"]

    def test_visit_seen_slightly_early_can_be_completed(
        self, client, clinic, make_appointment
    ):
        appointment = make_appointment(
            clinic["session"], clinic["patient"]["id"], _at(minutes=30)
        )

        response = _patch_appointment(
            client, clinic, appointment["id"], status="completed"
        )

        assert response.status_code == 200, response.get_json()

    def test_rejects_rescheduling_into_the_past(self, client, clinic, make_appointment):
        appointment = make_appointment(clinic["session"], clinic["patient"]["id"])

        response = _patch_appointment(
            client, clinic, appointment["id"], scheduled_at=_at(days=-2)
        )

        assert response.status_code == 422
        assert _field_error(response, "scheduled_at")

    def test_next_visit_booked_on_completion_must_be_in_the_future(
        self, client, clinic, make_follow_up
    ):
        follow_up = make_follow_up(clinic["session"], clinic["patient"]["id"], _day(0))

        response = client.post(
            f"/api/v1/follow-ups/{follow_up['id']}/complete",
            headers=clinic["headers"],
            json={"scheduled_at": _at(days=-5)},
        )

        assert response.status_code == 422
        assert _field_error(response, "scheduled_at")

    def test_rejected_next_visit_leaves_follow_up_open(
        self, client, clinic, make_follow_up
    ):
        """Completion is all-or-nothing: a bad booking completes nothing."""
        follow_up = make_follow_up(clinic["session"], clinic["patient"]["id"], _day(0))
        client.post(
            f"/api/v1/follow-ups/{follow_up['id']}/complete",
            headers=clinic["headers"],
            json={"scheduled_at": _at(days=-5)},
        )

        listed = client.get(
            f"/api/v1/patients/{clinic['patient']['id']}/follow-ups",
            headers=clinic["headers"],
        ).get_json()["data"]

        assert listed[0]["status"] == "upcoming"


class TestFollowUpDates:
    def _create(self, client, clinic, follow_up_date):
        return client.post(
            "/api/v1/follow-ups",
            headers=clinic["headers"],
            json={
                "patient_id": clinic["patient"]["id"],
                "follow_up_date": follow_up_date,
                "reason": "Review results",
            },
        )

    def test_rejects_a_past_date(self, client, clinic):
        """Reproduces the demo bug: a follow-up created for 2020."""
        response = self._create(client, clinic, "2020-01-01")

        assert response.status_code == 422
        assert _field_error(response, "follow_up_date")

    def test_accepts_today(self, client, clinic):
        assert self._create(client, clinic, _day(0)).status_code == 201

    def test_tolerates_yesterday_for_clinics_behind_utc(self, client, clinic):
        assert self._create(client, clinic, _day(-1)).status_code == 201

    def test_rejects_two_days_ago(self, client, clinic):
        assert self._create(client, clinic, _day(-2)).status_code == 422

    def test_rejects_more_than_two_years_ahead(self, client, clinic):
        assert self._create(client, clinic, _day(800)).status_code == 422

    def test_cannot_move_an_open_follow_up_into_the_past(
        self, client, clinic, make_follow_up
    ):
        follow_up = make_follow_up(clinic["session"], clinic["patient"]["id"], _day(5))

        response = client.patch(
            f"/api/v1/follow-ups/{follow_up['id']}",
            headers=clinic["headers"],
            json={"follow_up_date": "2020-01-01"},
        )

        assert response.status_code == 422


# --- Rule 5: one patient cannot be double-booked


class TestDoubleBooking:
    def test_rejects_same_patient_at_the_same_time(self, client, clinic):
        """Reproduces the demo bug: two bookings in the exact same slot."""
        when = _at(days=4)
        assert _book(client, clinic, when).status_code == 201

        response = _book(client, clinic, when)

        assert response.status_code == 409
        assert _field_error(response, "scheduled_at")

    def test_rejects_same_patient_within_thirty_minutes(self, client, clinic):
        assert _book(client, clinic, _at(days=4)).status_code == 201

        assert _book(client, clinic, _at(days=4, minutes=20)).status_code == 409

    def test_allows_same_patient_later_that_day(self, client, clinic):
        assert _book(client, clinic, _at(days=4)).status_code == 201

        assert _book(client, clinic, _at(days=4, hours=2)).status_code == 201

    def test_allows_different_patients_at_the_same_time(self, client, clinic):
        """Several practitioners can see different patients at once."""
        when = _at(days=4)
        assert _book(client, clinic, when).status_code == 201

        response = _book(client, clinic, when, patient=clinic["other_patient"])

        assert response.status_code == 201

    def test_cancelled_appointment_frees_the_slot(self, client, clinic):
        when = _at(days=4)
        first = _book(client, clinic, when).get_json()["data"]
        _patch_appointment(client, clinic, first["id"], status="cancelled")

        assert _book(client, clinic, when).status_code == 201

    def test_rejects_rescheduling_onto_another_booking(
        self, client, clinic, make_appointment
    ):
        when = _at(days=6)
        make_appointment(clinic["session"], clinic["patient"]["id"], when)
        second = make_appointment(clinic["session"], clinic["patient"]["id"], _at(days=9))

        response = _patch_appointment(client, clinic, second["id"], scheduled_at=when)

        assert response.status_code == 409

    def test_an_appointment_does_not_clash_with_itself(
        self, client, clinic, make_appointment
    ):
        appointment = make_appointment(
            clinic["session"], clinic["patient"]["id"], _at(days=6)
        )

        response = _patch_appointment(
            client,
            clinic,
            appointment["id"],
            scheduled_at=_at(days=6, minutes=15),
        )

        assert response.status_code == 200, response.get_json()

    def test_next_visit_on_completion_cannot_clash(
        self, client, clinic, make_follow_up
    ):
        when = _at(days=10)
        assert _book(client, clinic, when).status_code == 201
        follow_up = make_follow_up(clinic["session"], clinic["patient"]["id"], _day(0))

        response = client.post(
            f"/api/v1/follow-ups/{follow_up['id']}/complete",
            headers=clinic["headers"],
            json={"scheduled_at": when},
        )

        assert response.status_code == 409

"""
Seed fictional demonstration data through the HTTP API.

Deliberately not direct database inserts: going through the API means the
seed exercises the same validation, scoping, and status rules as real
use, so it cannot create a row the application itself would reject.

All names and contact details are invented. Run against a development
database only.
"""

import random
import sys
from datetime import date, datetime, time, timedelta, timezone

import urllib.error
import urllib.request
import json

BASE = "http://127.0.0.1:5000/api/v1"
TZ = timezone(timedelta(hours=3)) 

FIRST = ["Grace", "Daniel", "Amina", "Peter", "Faith", "Joseph", "Mercy",
         "Samuel", "Esther", "Brian", "Naomi", "Kevin", "Lydia", "Isaac"]
LAST = ["Wanjiru", "Otieno", "Kamau", "Achieng", "Mwangi", "Odhiambo",
        "Njoroge", "Akinyi", "Kiprop", "Wambui", "Omondi", "Chepkoech"]

REASONS = [
    "Review blood pressure readings",
    "Check on medication side effects",
    "Follow up on lab results",
    "Post-treatment review",
    "Repeat prescription review",
    "Check wound healing",
]


def call(path, payload=None, token=None, method=None):
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        method=method or ("POST" if data else "GET"),
        headers={
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        body = json.loads(error.read())
        print(f"  {path} -> {error.code} {body.get('message')}")
        return body


def main():
    email = f"demo{random.randint(1000, 9999)}@clinicflow.test"
    print(f"Registering clinic as {email}")

    auth = call("/auth/register", {
        "clinic_name": "Meridian Family Clinic",
        "full_name": "Ada Mwangi",
        "email": email,
        "password": "correct-horse-battery",
    })
    if not auth.get("success"):
        sys.exit("Registration failed. Is the backend running?")

    token = auth["data"]["access_token"]
    today = datetime.now(TZ).date()

    patients = []
    for _ in range(14):
        name = f"{random.choice(FIRST)} {random.choice(LAST)}"
        birth = date(random.randint(1955, 2015), random.randint(1, 12), random.randint(1, 28))
        result = call("/patients", {
            "full_name": name,
            "date_of_birth": birth.isoformat(),
            "gender": random.choice(["male", "female", "undisclosed"]),
            "phone": f"+2547{random.randint(10000000, 99999999)}",
        }, token)
        if result.get("success"):
            patients.append(result["data"])
    print(f"Created {len(patients)} patients")

    appointments = []
    for offset in range(-6, 9):
        day = today + timedelta(days=offset)
        for _ in range(random.randint(0, 4)):
            slot = datetime.combine(
                day, time(random.randint(8, 16), random.choice([0, 30])), tzinfo=TZ
            )
            result = call("/appointments", {
                "patient_id": random.choice(patients)["id"],
                "scheduled_at": slot.isoformat(),
                "appointment_type": random.choice(
                    ["consultation", "check_up", "follow_up"]
                ),
            }, token)
            if not result.get("success"):
                continue
            appointment = result["data"]

            if offset < 0:
                status = random.choices(
                    ["completed", "no_show", "cancelled"], [8, 1, 1]
                )[0]
            else:
                status = random.choice(["scheduled", "scheduled", "confirmed"])

            if status != "scheduled":
                call(f"/appointments/{appointment['id']}",
                     {"status": status}, token, method="PATCH")
            appointments.append(appointment)
    print(f"Created {len(appointments)} appointments")

    spread = [-9, -5, -2, 0, 0, 3, 8, 15, 21]
    created = 0
    for offset in spread:
        result = call("/follow-ups", {
            "patient_id": random.choice(patients)["id"],
            "follow_up_date": (today + timedelta(days=offset)).isoformat(),
            "reason": random.choice(REASONS),
        }, token)
        if result.get("success"):
            created += 1

    for _ in range(2):
        result = call("/follow-ups", {
            "patient_id": random.choice(patients)["id"],
            "follow_up_date": (today - timedelta(days=12)).isoformat(),
            "reason": random.choice(REASONS),
        }, token)
        if result.get("success"):
            call(f"/follow-ups/{result['data']['id']}/complete", {}, token)
            created += 1
    print(f"Created {created} follow-ups")

    print(f"\nSign in with:\n  {email}\n  correct-horse-battery")


if __name__ == "__main__":
    main()

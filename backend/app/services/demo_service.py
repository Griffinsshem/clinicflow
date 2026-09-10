import random
import secrets
from datetime import date, datetime, time, timedelta, timezone

from app.extensions import db
from app.models.appointment import Appointment
from app.models.clinic import Clinic
from app.models.enums import (
    AppointmentStatus,
    AppointmentType,
    FollowUpStatus,
    Gender,
    UserRole,
)
from app.models.follow_up import FollowUp
from app.models.patient import Patient
from app.models.user import User

_FIRST_NAMES = [
    "Grace", "Daniel", "Amina", "Peter", "Faith", "Joseph", "Mercy",
    "Samuel", "Esther", "Brian", "Naomi", "Kevin", "Lydia", "Isaac",
]
_LAST_NAMES = [
    "Wanjiru", "Otieno", "Kamau", "Achieng", "Mwangi", "Odhiambo",
    "Njoroge", "Akinyi", "Kiprop", "Wambui", "Omondi", "Chepkoech",
]
_REASONS = [
    "Review blood pressure readings",
    "Check on medication side effects",
    "Follow up on lab results",
    "Post-treatment review",
    "Repeat prescription review",
    "Check wound healing",
]

PATIENT_COUNT = 14
DAY_RANGE = range(-6, 9)
FOLLOW_UP_OFFSETS = [-9, -5, -2, 0, 0, 3, 8, 15, 21]


def _full_name() -> str:
    return f"{random.choice(_FIRST_NAMES)} {random.choice(_LAST_NAMES)}"


def create_demo_clinic(timezone_offset_minutes: int = 0) -> tuple[Clinic, User, str]:
    tz = timezone(timedelta(minutes=timezone_offset_minutes))
    today = datetime.now(tz).date()

    clinic = Clinic(name="Meridian Family Clinic")
    db.session.add(clinic)
    db.session.flush()  # assigns clinic.id without committing

    suffix = secrets.token_hex(4)
    password = secrets.token_urlsafe(16)

    user = User(
        clinic_id=clinic.id,
        full_name="Ada Mwangi",
        email=f"demo-{suffix}@clinicflow.example",
        role=UserRole.ADMIN,
    )
    user.set_password(password)
    db.session.add(user)

    patients = _seed_patients(clinic.id)
    db.session.flush()

    appointments = _seed_appointments(clinic.id, patients, today, tz)
    db.session.flush()

    _seed_follow_ups(clinic.id, patients, appointments, today)

    db.session.commit()
    return clinic, user, password


def _seed_patients(clinic_id: int) -> list[Patient]:
    patients = []
    for _ in range(PATIENT_COUNT):
        patient = Patient(
            clinic_id=clinic_id,
            full_name=_full_name(),
            date_of_birth=date(
                random.randint(1955, 2015), random.randint(1, 12), random.randint(1, 28)
            ),
            gender=random.choice(list(Gender)),
            phone=f"+2547{random.randint(10_000_000, 99_999_999)}",
        )
        db.session.add(patient)
        patients.append(patient)
    return patients


def _seed_appointments(
    clinic_id: int, patients: list[Patient], today: date, tz: timezone
) -> list[Appointment]:
    appointments = []

    for offset in DAY_RANGE:
        day = today + timedelta(days=offset)
        for _ in range(random.randint(0, 3)):
            slot = datetime.combine(
                day,
                time(random.randint(8, 16), random.choice([0, 30])),
                tzinfo=tz,
            )
            if offset < 0:
                status = random.choices(
                    [
                        AppointmentStatus.COMPLETED,
                        AppointmentStatus.NO_SHOW,
                        AppointmentStatus.CANCELLED,
                    ],
                    weights=[8, 1, 1],
                )[0]
            else:
                status = random.choice(
                    [
                        AppointmentStatus.SCHEDULED,
                        AppointmentStatus.SCHEDULED,
                        AppointmentStatus.CONFIRMED,
                    ]
                )

            appointment = Appointment(
                clinic_id=clinic_id,
                patient_id=random.choice(patients).id,
                scheduled_at=slot,
                appointment_type=random.choice(list(AppointmentType)),
                status=status,
            )
            db.session.add(appointment)
            appointments.append(appointment)

    return appointments


def _seed_follow_ups(
    clinic_id: int,
    patients: list[Patient],
    appointments: list[Appointment],
    today: date,
) -> None:
    completed_appointments = [
        a for a in appointments if a.status == AppointmentStatus.COMPLETED
    ]

    for offset in FOLLOW_UP_OFFSETS:
        source = (
            random.choice(completed_appointments)
            if completed_appointments and random.random() < 0.5
            else None
        )
        patient_id = source.patient_id if source else random.choice(patients).id

        db.session.add(
            FollowUp(
                clinic_id=clinic_id,
                patient_id=patient_id,
                appointment_id=source.id if source else None,
                follow_up_date=today + timedelta(days=offset),
                reason=random.choice(_REASONS),
                status=FollowUpStatus.UPCOMING,
            )
        )
    for _ in range(2):
        db.session.add(
            FollowUp(
                clinic_id=clinic_id,
                patient_id=random.choice(patients).id,
                follow_up_date=today - timedelta(days=random.randint(10, 20)),
                reason=random.choice(_REASONS),
                status=FollowUpStatus.COMPLETED,
            )
        )

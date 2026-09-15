# ClinicFlow

Appointment and follow-up management for small clinics.

**[Live demo](https://clinicflow-mu-nine.vercel.app)** — one click opens a private clinic with sample data. No signup.

![ClinicFlow dashboard](docs/screenshots/dashboard.png)

---

## The problem

Small clinics run on a paper diary, a phone, and someone's memory. That works for today's appointments. It does not work for the patient who was told to come back in six weeks.

The failure is specific: someone attends once, needs reviewing, and is never contacted again. Nobody decides to drop them — the note is in a diary nobody reopens. ClinicFlow is built around that one problem. Appointments and patient records exist to support it, not the other way round.

It is deliberately **not** a hospital management system. There is no billing, no inventory, no prescriptions, no lab results. Four capabilities, each finished.

## What it does

| | |
|---|---|
| **Patients** | Records with search, pagination, and a full visit history per person |
| **Appointments** | Scheduling with validated status transitions and date, status and type filters |
| **Follow-ups** | Commitments to see someone again, grouped by urgency, completed atomically with the next booking |
| **Dashboard** | Today's schedule, outstanding follow-ups, and the week's shape |

Every record belongs to a clinic, and no clinic can see another's data — enforced in the database schema, not only in application code. See [clinic isolation](#clinic-isolation-the-central-design-decision) below.

## Stack

**Frontend** — Next.js 16 (App Router), TypeScript strict mode, Tailwind CSS v4  
**Backend** — Flask, SQLAlchemy 2, Alembic, Pydantic v2, PostgreSQL 16  
**Deployment** — Vercel (frontend), Render (API), Neon (database)

99 backend tests, 15 of them covering cross-tenant isolation specifically.

---

## Architecture

```
Browser
   |  httpOnly cookie, same-origin requests only
   v
Next.js on Vercel
   |  Server-side proxy attaches the JWT as a Bearer token
   v
Flask on Render
   |  DATABASE_URL
   v
PostgreSQL on Neon
```

The browser never contacts the API directly. Every data request goes to `/api/proxy/...` on the Vercel origin, where a Next.js route handler reads the session cookie — which client JavaScript cannot — and forwards the call server-to-server. See [why the token is not in localStorage](#why-the-token-is-not-in-localstorage).

### Repository layout

```
backend/
  app/
    models/      SQLAlchemy models, enums, shared columns
    routes/      Thin HTTP handlers
    services/    Business logic, framework-independent
    schemas/     Pydantic request validation
    utils/       Scoping, decorators, response envelope
  migrations/    Alembic revisions
  tests/         99 tests

frontend/
  app/
    (auth)/      Login, register
    (app)/       Dashboard, patients, appointments, follow-ups
    api/         Auth handlers and the authenticated proxy
  components/    UI primitives and feature components
  lib/           API clients, formatting, session handling
  proxy.ts       Edge route protection
```

---

## Design decisions worth explaining

### Clinic isolation: the central design decision

Multi-tenant isolation is usually a `WHERE clinic_id = ?` in the service layer. That works until someone writes a query without it — and nothing in the database objects.

ClinicFlow enforces it structurally. Every patient carries a `UNIQUE (id, clinic_id)` constraint, and appointments reference **that pair** rather than the patient ID alone:

```python
ForeignKeyConstraint(
    ["patient_id", "clinic_id"],
    ["patients.id", "patients.clinic_id"],
    ondelete="CASCADE",
)
```

The consequence: an appointment whose `clinic_id` disagrees with its patient's cannot be written at all. PostgreSQL rejects it.

```
ERROR:  insert or update on table "appointments" violates foreign key
        constraint "fk_appointments_patient_clinic"
DETAIL:  Key (patient_id, clinic_id)=(1, 2) is not present in table "patients".
```

Two independent layers protect tenancy. The schema stops corruption; a query-scoping helper (`app/utils/scoping.py`) stops disclosure by ensuring every read is filtered by the authenticated user's clinic. Neither substitutes for the other.

Cross-clinic reads return **404, not 403**. A 403 confirms the record exists, letting an attacker map the ID space by probing. From another clinic's perspective, the record simply does not exist.

`tests/test_clinic_isolation.py` asserts all of this through the HTTP API — the same path an attacker would use.

### Why `overdue` is computed, not stored

A follow-up is overdue when its date has passed and it is still open. The obvious approach is a `status` column with an `overdue` value.

That is wrong. The moment midnight passes, stored values are stale. Keeping them correct needs a scheduled job, and between runs the database disagrees with reality — for a product whose entire purpose is not losing track of patients, that is the worst possible failure.

Only `upcoming` and `completed` are stored. `overdue` is derived from `follow_up_date < today AND status = 'upcoming'`, evaluated per request. Correct by construction, no job to run.

"Today" means the **clinic's** today. The API accepts a `tz_offset` parameter, because a server in UTC would mark a Nairobi follow-up overdue three hours early.

### Why the token is not in localStorage

The conventional approach stores a JWT in `localStorage` and attaches it to each request. It is simpler, and any XSS bug — in your code or any dependency — can read it.

ClinicFlow puts the token in an **httpOnly cookie** set by a Next.js route handler. JavaScript cannot read it. The browser talks only to same-origin `/api/proxy/...` routes, which attach the token server-side.

That buys two things. An XSS bug cannot exfiltrate the session. And `proxy.ts` can see the cookie, so route protection happens at the edge before a page renders — no flash of a dashboard shell before a client-side redirect.

The cost is a proxy layer and CSRF consideration. The cookie is `sameSite=lax`, which stops the browser sending it on cross-site writes, and the proxy independently verifies the Origin header on mutating requests.

### Aggregate-only dashboard queries

The dashboard issues nine SQL statements regardless of clinic size. Every metric is a `COUNT(*)`; the weekly chart is a single `GROUP BY`. Only two queries return rows, both with a `LIMIT`.

`len(Patient.query.all())` gives the same number and loads every row to get it. Indistinguishable at twelve patients, unusable at fifty thousand.

### Other choices

**Status transitions are validated.** An appointment cannot go from `cancelled` to `completed`. The rules live in `appointment_service.py`; the UI shows only reachable options so staff never click something that fails.

**Completing a follow-up and booking the next visit is one transaction.** Two separate calls would leave a window where the follow-up is done and no appointment exists — silently dropping the patient, which is the paper-records failure being replaced.

**Enums are VARCHAR + CHECK, not native PostgreSQL enums.** Native enums need `ALTER TYPE` to change and Alembic autogenerates them poorly. Same integrity, ordinary DDL.

**The demo creates a fresh clinic per visitor.** A shared demo account means shared mutable state: one visitor deletes a patient, the next sees it missing. Per-visitor clinics need no reset job and exercise the same isolation guarantees as a real signup.

---

## Screenshots

| Follow-ups — the work queue | Patient detail |
|---|---|
| ![Follow-ups](docs/screenshots/follow-ups.png) | ![Patient detail](docs/screenshots/patient-detail.png) |

![Landing page](docs/screenshots/landing.png)

---

## Running locally

Requires Python 3.11+, Node 20+, and PostgreSQL 15+ (15 minimum — the schema uses `ON DELETE SET NULL (column)`, added in 15).

### Database

```bash
# Ubuntu/Debian
sudo apt install -y postgresql postgresql-contrib libpq-dev
sudo -u postgres createuser --pwprompt clinicflow
sudo -u postgres createdb --owner=clinicflow clinicflow_dev
sudo -u postgres createdb --owner=clinicflow clinicflow_test

# macOS
brew install postgresql@16 && brew services start postgresql@16
createuser --pwprompt clinicflow
createdb --owner=clinicflow clinicflow_dev
createdb --owner=clinicflow clinicflow_test
```

Two databases: the test suite truncates its own between tests and must never touch development data.

### Backend

```bash
cd backend
python3 -m venv .venv        # Ubuntu: sudo apt install python3.12-venv first
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env         # then fill in the values below
flask db upgrade
python run.py                # http://127.0.0.1:5000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev                  # http://localhost:3000
```

### Tests

```bash
cd backend && pytest -q                       # 99 tests
pytest tests/test_clinic_isolation.py -v      # the isolation suite
```

---

## Environment variables

### Backend (`backend/.env`)

| Variable | Purpose |
|---|---|
| `FLASK_ENV` | `development`, `testing`, or `production` |
| `SECRET_KEY` | Flask session signing. Must differ from the JWT key. |
| `JWT_SECRET_KEY` | Access token signing |
| `DATABASE_URL` | `postgresql+psycopg://user:pass@host/db` |
| `TEST_DATABASE_URL` | Separate database for the test suite |
| `CORS_ORIGINS` | Comma-separated allowlist. No wildcards. |
| `JWT_ACCESS_TOKEN_EXPIRES_MINUTES` | Token lifetime, default 60 |
| `DEMO_ENABLED` | Exposes `POST /api/v1/demo` |

Generate secrets with `python -c "import secrets; print(secrets.token_urlsafe(64))"`.

In production, `app/config.py` validates these at boot and **refuses to start** if a secret is missing, still a placeholder, or if `CORS_ORIGINS` contains a wildcard. A crashed deploy is visible; one running on `change-me` is not.

### Frontend (`frontend/.env.local`)

| Variable | Purpose |
|---|---|
| `API_URL` | Backend base URL, e.g. `http://localhost:5000/api/v1` |

Note the absence of a `NEXT_PUBLIC_` prefix. The browser never contacts the API directly, so the backend URL stays server-only and out of the client bundle.

---

## API

All endpoints are under `/api/v1`. Everything except `/health`, `/auth/register`, `/auth/login` and `/demo` requires a Bearer token.

```
POST   /auth/register          Create a clinic and its first admin
POST   /auth/login             Exchange credentials for a token
GET    /auth/me                Current user and clinic

GET    /patients               ?search= &page= &limit=
POST   /patients
GET    /patients/:id
PATCH  /patients/:id
DELETE /patients/:id
GET    /patients/:id/appointments
GET    /patients/:id/follow-ups

GET    /appointments           ?date_from= &date_to= &status= &appointment_type=
POST   /appointments
GET    /appointments/:id
PATCH  /appointments/:id
DELETE /appointments/:id

GET    /follow-ups             ?grouped=true &overdue=true &status= &tz_offset=
POST   /follow-ups
PATCH  /follow-ups/:id
POST   /follow-ups/:id/complete    Completes and optionally books the next visit

GET    /dashboard              ?tz_offset=
POST   /demo                   Provisions a demo clinic (rate limited)
GET    /health
```

Every response uses one envelope:

```json
{ "success": true,  "data": {}, "meta": { "page": 1, "total": 42 } }
{ "success": false, "message": "Validation failed", "errors": { "email": "..." } }
```

Discriminated on `success`, so a narrowed check in TypeScript gives either `data` or `errors`, never both.

---

## Security

| | |
|---|---|
| Passwords | scrypt via Werkzeug. Hashes are never serialised — `to_dict()` has no branch that can emit one. |
| Tokens | JWT with expiry, in an httpOnly `sameSite=lax` cookie. Authorization re-reads the user from the database rather than trusting token claims, so revocation is immediate. |
| Isolation | Composite foreign keys plus a query-scoping helper. Cross-clinic access returns 404. |
| Validation | Pydantic with `extra="forbid"` — an unexpected field like `role` or `clinic_id` is a visible 422, not a silently ignored value. |
| Login | Uniform response for wrong password and unknown email, including a dummy hash computation so response timing cannot enumerate accounts. |
| SQL | SQLAlchemy throughout. The one raw statement is a parameterless `SELECT 1` in the health check. |
| CORS | Explicit origin allowlist from the environment. Production refuses to boot with a wildcard. |
| Rate limiting | 5 logins/minute, 3 registrations/hour, 3 demos/hour, per IP. |
| Errors | Full traceback to logs, generic message to the client. No stack traces, SQL, or paths in responses. |
| Logging | User and clinic IDs only. Never passwords, tokens, or patient identifiers. |

### Healthcare data scope

This is a portfolio project, not a medical record system. It stores only what scheduling requires: name, date of birth, gender, phone, email. No diagnoses, no clinical notes, no medical history. **All seeded and demo data is fictional.**

A production deployment serving real patients would need audit logging, encryption at rest, a data retention policy, a signed BAA with each provider, and a compliance review. The minimal scope here is a deliberate decision, not an oversight.

---

## Known limitations

Named rather than hidden. Each is a considered tradeoff for a portfolio deployment.

**Cold start.** The API sleeps after 15 minutes idle on Render's free tier; the first request then takes 30–60 seconds. The frontend detects this and explains the wait rather than showing a silent spinner. Production would use a paid instance.

**No token revocation.** Signing out deletes the cookie but the JWT stays valid until it expires, up to an hour. A revocation list needs a store (Redis) and a check on every request. For a one-hour window with an unreadable cookie, the trade seemed reasonable; a real deployment would add it.

**Rate limiting is per-instance.** Counters live in process memory. Correct on a single instance, but with replicas each holds its own count and the effective limit multiplies. Redis-backed storage is a one-line change to `storage_uri`.

**Hard deletes.** Deleting a patient removes their appointments and follow-ups via `ON DELETE CASCADE`. A clinical system would soft-delete for auditability — a `deleted_at` column and a filter in the scoping helper.

**Demo clinics are never cleaned up.** Each visitor's demo clinic persists. At portfolio traffic this is negligible; at scale it needs a scheduled cleanup of clinics older than a day.

**No role enforcement beyond the model.** `admin` and `staff` exist and an `admin_required` decorator is implemented, but no endpoint currently restricts by role — there is no user management feature yet to restrict.

**Patient selector loads 100 records.** The appointment scheduling dropdown fetches the first page of patients. Adequate for a pilot-scale clinic; a larger practice needs a searchable combobox querying as you type.

**Frontend tests are absent.** Backend coverage is thorough; the frontend is verified manually. Component and flow tests would be the next addition.

---

## Deployment

| | |
|---|---|
| Frontend | Vercel, root directory `frontend`, `API_URL` set in project settings |
| API | Render, `render.yaml` blueprint, gunicorn with migrations chained ahead of the server |
| Database | Neon, PostgreSQL 16, pooled connection |

The database is on Neon rather than Render because Render's free PostgreSQL is **deleted after 30 days** — which would silently break a portfolio link a month after deploying. Neon's free tier has no expiry and is ordinary Postgres, so the same migrations run unchanged.

Migrations run in `startCommand` rather than a pre-deploy hook, which Render reserves for paid tiers. Since `startCommand` is a single shell invocation, `flask db upgrade` completes before gunicorn execs and the workers it forks inherit a migrated database. The `&&` means a failed migration fails the deploy rather than serving traffic against a half-migrated schema.

---

## License

MIT
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

165 backend tests, 15 of them covering cross-tenant isolation specifically.

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
  tests/         165 tests

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

The cost is a proxy layer and CSRF consideration. The cookie is `sameSite=lax`, which stops the browser sending it on cross-site writes. That protects authenticated calls, but not the routes that *set* the cookie: another site could auto-submit a hidden form to `/api/auth/login` and sign a visitor into an attacker's account, start a demo session for them, or sign them out. So `proxy.ts` refuses every state-changing request to `/api/*` whose `Origin` does not match the host the browser addressed, including a missing or `null` Origin. It is checked once, centrally, so a route added later cannot forget it, and the data proxy repeats the check as a second layer. See [`frontend/lib/origin.ts`](frontend/lib/origin.ts).

### Security headers and a nonce-based CSP

ClinicFlow shows patient records, so a script that slipped into a page (from a compromised npm package, or a field that one day escaped React's escaping) could read them and send them anywhere. The Content-Security-Policy is built to make that fail:

- **Scripts need a per-request nonce.** `proxy.ts` generates a fresh random nonce for every page request and puts it in the policy; Next.js stamps it onto its own scripts while rendering. A script without the nonce does not run. There is no `'unsafe-inline'` for scripts, and no `'unsafe-eval'` outside development.
- **The page can only talk to its own origin** (`connect-src 'self'`). This is where the [proxy design](#why-the-token-is-not-in-localstorage) pays off a second time: the browser never calls the Flask API, so nothing else needs allowing, and stolen data has nowhere to go.
- **No framing, no plugins, no foreign forms** (`frame-ancestors 'none'`, `object-src 'none'`, `form-action 'self'`).

The cost: a nonce must be added while the page renders, so every page is now rendered per request (`await connection()` in the root layout) rather than served pre-built. The app pages were already dynamic, since they check the user's session, so in practice this only affects the landing and auth pages. That is the trade-off Next.js's own CSP guide recommends for applications handling sensitive data.

One allowance: inline style *attributes* (`style-src-attr 'unsafe-inline'`), because the dashboard chart sizes its bars with them. A style attribute cannot run code. `<style>` elements still need the nonce.

Alongside the CSP, every response carries `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin` (other sites never see a path like `/patients/42`), a `Permissions-Policy` that denies camera, microphone, location and similar features, and `Cross-Origin-Opener-Policy: same-origin`. `/api/*` responses are `Cache-Control: no-store`.

The Flask API adds its own on every response, errors included: `Cache-Control: no-store` (patient data is never kept by a browser, proxy or CDN), `nosniff`, `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'`, `X-Frame-Options: DENY` and `Referrer-Policy: no-referrer`. See [`frontend/lib/security-headers.ts`](frontend/lib/security-headers.ts) and [`backend/app/utils/security_headers.py`](backend/app/utils/security_headers.py).

To check a deployment: `node frontend/scripts/check-security-headers.mjs https://your-site.example`. It checks every header on the landing page, the login page, a 404 and an API route, confirms the nonce changes per request, and exits non-zero if anything is missing.

### Rate limiting behind a proxy

Because the browser never calls Flask, every request Flask sees comes from one of Vercel's shared outbound IPs. Keyed on that address, "3 demos per hour per IP" would really mean three demos per hour for *everyone*, and one person could exhaust the login limit for all users.

So the Next.js server forwards the visitor's real IP in `X-Client-IP`, together with a shared secret in `X-Proxy-Secret`. The API is publicly reachable, so anyone can send an `X-Client-IP` header; the secret is what makes it trustworthy. Without the correct secret, a request is attributed to its connecting address exactly as before, so forging the header cannot buy a fresh bucket. The secret is compared in constant time, the forwarded value must parse as an IP address, and production refuses to boot without a strong secret. See [`backend/app/utils/client_ip.py`](backend/app/utils/client_ip.py).

Login also has a second, per-account limit: 10 *failed* attempts per email per 15 minutes, across all IPs. The per-IP limit stops one machine hammering the endpoint; the per-account limit stops password guessing spread over many machines. Successful sign-ins do not count, so staff who sign in often are never locked out by it.

### Scheduling rules: a record has to make sense

Validating the *shape* of input (types, lengths, a timezone offset) is not enough: a correctly formatted appointment can still be nonsense. The demo showed it. A completed visit could be moved to 2030, a completed follow-up reopened, a follow-up linked to a different patient's appointment, a follow-up dated 2020, an appointment dated 2001, and the same patient booked twice at the same moment. Each one quietly corrupts the history a clinic relies on.

These rules live in one module, [`scheduling_rules.py`](backend/app/services/scheduling_rules.py), and every path that books or changes something calls them: creating and editing appointments, editing follow-ups, and completing a follow-up while booking the next visit.

| Rule | Why |
|---|---|
| Completed, cancelled and no-show appointments keep their date, time and type. Notes stay editable. A no-show can be rebooked. | What happened is history. Staff still add visit notes afterwards. |
| A follow-up's status changes only through **Complete**. A completed follow-up's date is fixed and it cannot be reopened. | Completing can also book the next visit in the same transaction; a PATCH that flips the status would skip that. |
| A follow-up can only link to an appointment of the same patient. | Otherwise the clinic's own records contradict each other. |
| New bookings must start no earlier than an hour ago (walk-ins) and no more than two years ahead. A visit can't be marked completed or no-show before it has happened. Past visits can still be recorded as completed. Follow-up dates run from today to two years out. | Catches typos (2062 for 2026) and states that can't be true, such as a follow-up overdue the moment it is created. |
| The same patient can't have two active appointments within 30 minutes. | A double booking for one person is always a mistake. Different patients at the same time are allowed, because a clinic may have several practitioners and ClinicFlow does not model practitioners or rooms. |

The edit form re-sends the date and type on every save, so the rules compare values (to the minute) rather than reacting to a field merely being present. Saving only a note on a completed visit works. The UI mirrors the rules in [`frontend/lib/scheduling.ts`](frontend/lib/scheduling.ts): date pickers have a minimum, and the status menu doesn't offer Completed or No-show for a visit still in the future.

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
cd backend && pytest -q                       # 165 tests
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
| `PROXY_SHARED_SECRET` | Shared with the frontend; lets it pass each visitor's real IP for rate limiting. Required in production, at least 32 characters, different from the other secrets |

Generate secrets with `python -c "import secrets; print(secrets.token_urlsafe(64))"`.

In production, `app/config.py` validates these at boot and **refuses to start** if a secret is missing, still a placeholder, or if `CORS_ORIGINS` contains a wildcard. A crashed deploy is visible; one running on `change-me` is not.

### Frontend (`frontend/.env.local`)

| Variable | Purpose |
|---|---|
| `API_URL` | Backend base URL, e.g. `http://localhost:5000/api/v1` |
| `PROXY_SHARED_SECRET` | Same value as the backend's. Optional locally; without it in production, rate limits fall back to Vercel's shared IPs |

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
| Rate limiting | Per visitor IP: 5 logins/minute, 3 registrations/hour, 3 demos/hour. Per account: 10 failed logins per 15 minutes. The visitor IP is forwarded by the frontend and trusted only with the shared proxy secret. |
| Security headers | Nonce-based CSP on every page (no inline or eval scripts, same-origin connections only, no framing), HSTS, `nosniff`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`. API responses are `no-store`. Checked by `frontend/scripts/check-security-headers.mjs`. |
| CSRF | Every state-changing `/api/*` request must carry an `Origin` matching the site, on top of the `sameSite=lax` cookie. Blocks login CSRF, forced demo sessions and forced sign-out. |
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

**Rate limiting is per-process.** Counters live in process memory, and gunicorn runs two workers, each with its own count, so the effective limits are up to double those stated; replicas would multiply them further. Redis-backed storage is a one-line change to `storage_uri`.

**The per-account login limit can be triggered by others.** Someone who knows a staff email can make 10 failed attempts and block sign-in to that account for 15 minutes. That is the standard trade-off for stopping distributed password guessing; a production system would add a CAPTCHA or email-based unlock rather than a hard lockout.

**Hard deletes.** Deleting a patient removes their appointments and follow-ups via `ON DELETE CASCADE`. A clinical system would soft-delete for auditability — a `deleted_at` column and a filter in the scoping helper.

**Demo clinics are never cleaned up.** Each visitor's demo clinic persists. At portfolio traffic this is negligible; at scale it needs a scheduled cleanup of clinics older than a day.

**No role enforcement beyond the model.** `admin` and `staff` exist and an `admin_required` decorator is implemented, but no endpoint currently restricts by role — there is no user management feature yet to restrict.

**Patient selector loads 100 records.** The appointment scheduling dropdown fetches the first page of patients. Adequate for a pilot-scale clinic; a larger practice needs a searchable combobox querying as you type.

**Clinic-wide double booking is not prevented.** The same patient can't be double-booked, but two different patients can share a time, because without practitioners, rooms or appointment durations the system can't know whether that's a clash. Adding a practitioner to appointments would make a per-practitioner rule possible. The per-patient check is also a read-then-write in the application; two simultaneous requests could both pass it. A PostgreSQL exclusion constraint would close that, at the cost of a fixed slot length.

**Vercel preview deployments and the CSP.** Vercel's feedback toolbar on preview deployments loads scripts from Vercel's own domain, which the CSP blocks, so the toolbar won't appear on previews. Production is unaffected. Allow `https://vercel.live` in `script-src`, `connect-src` and `frame-src` if the toolbar is wanted.

**Frontend tests are absent.** Backend coverage is thorough; the frontend is verified manually. Component and flow tests would be the next addition.

---

## Deployment

| | |
|---|---|
| Frontend | Vercel, root directory `frontend`, `API_URL` and `PROXY_SHARED_SECRET` set in project settings |
| API | Render, `render.yaml` blueprint, gunicorn with migrations chained ahead of the server |
| Database | Neon, PostgreSQL 16, pooled connection |

The database is on Neon rather than Render because Render's free PostgreSQL is **deleted after 30 days** — which would silently break a portfolio link a month after deploying. Neon's free tier has no expiry and is ordinary Postgres, so the same migrations run unchanged.

Migrations run in `startCommand` rather than a pre-deploy hook, which Render reserves for paid tiers. Since `startCommand` is a single shell invocation, `flask db upgrade` completes before gunicorn execs and the workers it forks inherit a migrated database. The `&&` means a failed migration fails the deploy rather than serving traffic against a half-migrated schema.

### Shared proxy secret

The frontend and API share one secret, `PROXY_SHARED_SECRET`, used to trust the forwarded visitor IP (see [rate limiting behind a proxy](#rate-limiting-behind-a-proxy)). It must be identical on both sides.

1. Generate it once: `python -c "import secrets; print(secrets.token_urlsafe(48))"`
2. Render → the API service → Environment: add `PROXY_SHARED_SECRET`.
3. Vercel → the project → Settings → Environment Variables: add `PROXY_SHARED_SECRET` with the same value, then redeploy.

Production refuses to boot without it. If a deploy reaches Render before the variable is set, that deploy fails its health check and Render keeps the previous version serving, so set the variable first.

To rotate it, set the new value on both sides and redeploy both. Between the two deploys, rate limits fall back to per-connection (as they were before this fix); nothing breaks.

---

## Changelog

What changed, why, and what each change needs at deploy time: see [CHANGELOG.md](CHANGELOG.md).

---

## License

MIT
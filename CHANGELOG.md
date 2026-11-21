# Changelog

Notable changes to ClinicFlow, newest first. Each entry says what changed,
why, and anything that has to be done when deploying it.

## 2026-11-21 — Data integrity rules for appointments and follow-ups

### Fixed

Bugs reproduced on the live demo. Each request below was accepted
before this change:

| Bug | Now |
|---|---|
| A completed appointment could be rescheduled (moved to 2030) and its type changed | 422. Completed, cancelled and no-show appointments keep their date, time and type. Notes stay editable. |
| A completed follow-up could be reopened with `PATCH {"status": "upcoming"}` | 422. Status changes only through Complete; a completed follow-up is not reopened and its date is fixed. |
| A follow-up could link to another patient's appointment | 422 on `appointment_id`. |
| A follow-up dated 2020 and an appointment dated 2001 were accepted | 422. See the date rules below. |
| The same patient could be booked twice in the same slot | 409 when the same patient has another active appointment within 30 minutes. |

Date rules (`backend/app/services/scheduling_rules.py`):
- New bookings can start up to 1 hour ago (walk-ins) and up to 2 years ahead.
- Past visits can still be recorded as completed (back-entry), up to 5 years back.
- A visit can't be marked completed more than 1 hour before it starts, or a no-show before it starts.
- Follow-up dates run from today (with one day of tolerance for clinics behind UTC) to 2 years ahead.
- Completing a follow-up and booking the next visit applies the same rules, and a rejected booking now leaves the follow-up untouched (it is checked before anything changes).

### Changed (frontend)

- New `frontend/lib/scheduling.ts` mirrors the rules so the UI doesn't offer actions the API refuses.
- The status menu no longer offers Completed or No-show for a visit still in the future.
- Date pickers for booking, the next visit and follow-ups have a minimum date. The follow-up default date now uses the local date rather than UTC.
- The appointment form locks date and type for finished appointments and sends only the notes. The UI doesn't currently open this form for editing, so this takes effect once editing is added.

### Tests

- `backend/tests/test_scheduling_rules.py`: 39 tests, one group per rule, including each reproduced bug. 24 of them fail against the previous code; the other 15 check that legitimate actions still work.
- Existing tests used fixed dates (`2026-11-01`, `2026-12-01`) that were becoming past dates. Fixtures now use relative dates and build past state (an overdue follow-up, yesterday's visit) directly in the database, because the API now rightly refuses to create it.
- 156 backend tests in total, all passing.
- Verified end to end against a production build: all five original bugs are refused with clear messages, and the status menu offers Completed and No-show only for visits that have happened.

### Not changed

- Different patients at the same time are still allowed (a clinic can have several practitioners). See README, Known limitations.

### Deploying this change

Nothing extra: no migrations and no new environment variables.

## 2026-11-21 — Per-visitor rate limiting and CSRF protection

### Security

**Rate limits now apply per visitor, not to everyone at once.**
The browser never calls the API directly; every request comes from the
Next.js server on Vercel. Flask therefore saw only Vercel's shared outbound
IPs and keyed every rate limit on them. In practice "3 demos per hour per
IP" meant roughly three demos per hour for all visitors combined, and one
person could exhaust the login limit for everybody.

- The Next.js server now forwards the visitor's IP (`X-Client-IP`) with a
  shared secret (`X-Proxy-Secret`) on login, register, demo and proxied
  API calls (`frontend/lib/client-ip.ts`, `frontend/lib/backend.ts`).
- The API's limiter keys on that IP only when the secret matches, compared
  in constant time, and the value parses as an IP address. Otherwise it
  uses the connecting address as before, so forging the header gains
  nothing (`backend/app/utils/client_ip.py`, `backend/app/extensions.py`).
- New per-account login limit: 10 failed attempts per email per 15
  minutes across all IPs, to stop password guessing spread over many
  machines. Successful sign-ins are not counted
  (`backend/app/routes/auth.py`).
- Production refuses to start unless `PROXY_SHARED_SECRET` is set, at
  least 32 characters, not a placeholder, and different from the other
  secrets (`backend/app/config.py`).

**Cross-site requests to the app's own API routes are refused.**
The session cookie is `sameSite=lax`, which protects authenticated calls
but not the routes that *set* the cookie. Another site could auto-submit a
hidden form (even smuggling a JSON body as `text/plain`) to sign a visitor
into an attacker's account ("login CSRF"), start a demo session for them,
or sign them out. Only the data proxy checked the `Origin` header.

- `frontend/proxy.ts` now checks every state-changing request to `/api/*`
  and returns 403 unless its `Origin` matches the host the browser
  addressed. A missing or `null` Origin is refused. One central check
  means a route handler added later is covered automatically.
- The shared logic lives in `frontend/lib/origin.ts`; the data proxy route
  uses it as a second layer.
- The check compares the Origin's host with the `Host` /
  `X-Forwarded-Host` header rather than with `request.url`. The server
  rebuilds `request.url` from its own idea of its hostname (often
  `localhost`), which wrongly blocked legitimate requests in testing.

### Tests

- `backend/tests/test_rate_limiting.py` adds 18 tests (117 total, all
  passing). They cover IP resolution with and without the secret, forged
  and malformed headers, per-visitor demo limits, the per-account login
  limit, and the production boot checks. The per-visitor tests were
  confirmed to fail against the old configuration.
- Verified end to end against the real Flask API and a production build of
  the frontend. Cross-site login, register, demo, logout and proxy calls
  all return 403. Normal sign-up, sign-in, sign-out, the demo button and
  creating a patient all still work in a real browser. A visitor's 4th
  demo in an hour gets 429 while a different visitor still gets in.

### Docs

- README: new "Rate limiting behind a proxy" section, updated CSRF
  explanation, security table, environment variables, known limitations
  and deployment steps.
- `backend/.env.example`, `frontend/.env.example` and `render.yaml` list
  `PROXY_SHARED_SECRET`. `render.yaml` marks it `sync: false` because the
  value must match Vercel's.

### Deploying this change

Set `PROXY_SHARED_SECRET` **before** merging (see README, "Shared proxy
secret"):

1. Generate: `python -c "import secrets; print(secrets.token_urlsafe(48))"`
2. Add it to the Render API service's environment.
3. Add the same value to the Vercel project's environment variables.

If Render deploys without it, the new version refuses to boot and Render
keeps the previous version serving. If only Vercel is missing it, the site
works but rate limits fall back to Vercel's shared IPs.

## 2026-11-21 — Error, loading and not-found screens

### Added

- `app/not-found.tsx`: 404 page for unknown URLs. Signed-in users are
  pointed to the dashboard; everyone else to the landing page.
- `app/error.tsx`: root error boundary for the landing and auth pages and
  for errors thrown by the app shell layout. Shows the error digest as a
  reference for matching server logs.
- `app/(app)/error.tsx`: in-app error boundary that keeps the navigation
  usable.
- `app/global-error.tsx`: last-resort boundary for root layout failures.
- `app/loading.tsx`: full-page loader shown while the app checks sign-in.
  Replaces a blank screen during the API's cold start; a "server is waking
  up" hint appears after 5 seconds, using a CSS delay so it works before
  JavaScript loads.
- `app/(app)/loading.tsx`: in-shell page skeleton between navigations.
- `components/ui/StatusScreen.tsx`: shared layout for these screens.

# Build status

Last updated: 3 Nov 2026. Legend: **Done** = built and its testing step passed; **Partial** = built, but some of
the testing step or acceptance criteria are not done yet (noted); **Not started**.

## Sprint 0: Setup
| Task | Status | Notes |
|---|---|---|
| S0-T01 Repository and tooling | Partial | Layout, `.gitignore`, `.env.example` done. No pre-commit hooks, Prettier or "fail if .env tracked" CI check yet. |
| S0-T02 Supabase project and local stack | Partial | Local stack works. A hosted project exists (`hgcvaekiwlbqwcgchjos`) but the migrations are **not applied to it yet** and the app isn't pointed at it: follow docs/07-hosted-supabase-setup.md. |
| S0-T03 Backend skeleton | Done | `/health`, error shape, CORS, settings. Tested. |
| S0-T04 JWT authentication | Done | HS256 (local) tested with real tokens; ES256/JWKS (what your hosted project uses) tested with a generated key, including rejection of a wrong key and of an HS256 downgrade. The live JWKS fetch from your project was confirmed to work. |
| S0-T05 Frontend skeleton | Partial | Vite + React + TS + Tailwind + Router + Query + Vitest work; build and lint pass. Prettier not set up. |
| S0-T06 Auth client + protected routes | Partial | Verified in a real browser (register, login redirect, `/me`). No Playwright test yet. |
| S0-T07 Migration and seed workflow | Partial | Migrations and template seed work and re-apply cleanly. No `seed-test` script (tests create their own users). |
| S0-T08 CI | Partial | `.github/workflows/ci.yml` written; never run (no remote yet). |
| S0-T09 RLS test harness | Done | RLS tested directly through PostgREST as user A, user B and anonymous (`test_api_integration.py`). |
| S0-T10 Deployment (staging) | Not started | Needs hosting decisions. |

## Sprint 1: Auth, challenges, check-ins
| Task | Status | Notes |
|---|---|---|
| S1-T01 Sign-up and log-in | Partial | Works in the browser end to end. No component tests for the forms yet. |
| S1-T02 Session and logout | Done | Reload keeps the session; logout returns to `/login`. Verified in the browser. |
| S1-T03 Password reset | Done | Verified end to end: request, email from local mail catcher, link, new password, old password rejected. |
| S1-T04 Profile settings | Partial | API tested (validation, timezone, role never writable). Settings screen built, not yet exercised in the browser. |
| S1-T05 Create a challenge | Done | API validation tested; create flow verified in the browser. |
| S1-T06 Winter Arc template | Done | Template seeded, copy verified, template immutable (also through RLS). |
| S1-T07 Add, rename, reorder goals | Partial | API fully tested. UI built; add/rename/reorder not yet clicked through in the browser. No drag-and-drop (up/down buttons). |
| S1-T08 Retire and delete goals | Partial | API tested incl. windows and confirmation. Dialogs not yet exercised in the browser. |
| S1-T09 Edit, archive, delete challenge | Partial | API tested (409 when dates exclude logged days). Settings tab not yet exercised in the browser. |
| S1-T10 Log today | Done | Tested in API (idempotent, last write wins, timezone) and the browser (set, clear, persists across reload). Mobile viewport not checked. |
| S1-T11 Backfill past days | Partial | API boundary tests done. Date picker UI built, not exercised in the browser. |
| S1-T12 Check-in grid | Partial | Renders and cycles cells in the browser. 366 x 15 performance not measured. |
| S1-T13 Data isolation tests | Done | 12 cross-user probes return 404; direct-database RLS tests; one probe was mutation-checked (removing the owner filter makes the test fail). |

## Test inventory
- Backend: 28 unit + 21 integration (against local Supabase) = 49 passing. Integration tests refuse to run against a hosted project.
- Frontend: 24 passing (dates, status control, route guards, API client).
- Not yet: Playwright end-to-end, axe accessibility checks, performance checks.

## Known gaps and decisions
- The Python backend uses the service-role key (bypasses RLS), so every repository query is scoped to the caller; RLS stays on as a second layer.
- Multi-step writes (e.g. changing a challenge's dates then realigning goal windows) are separate requests, not one transaction. Fine at this scale; move to a SQL function if it ever matters.
- One integration test (`test_entry_date_rules`) failed once out of about 20 full runs and could not be reproduced. Watch for flakiness.
- "Today" is pending until the day ends in the scoring rules (Sprint 2); the logging screens already use the user's timezone for "today".

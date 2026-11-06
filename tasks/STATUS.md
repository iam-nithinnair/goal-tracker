# Build status

Last updated: 5 Nov 2026. Legend: **Done** = built and its testing step passed; **Partial** = built, but some of
the testing step or acceptance criteria are not done yet (noted); **Not started**.

## Sprint 0: Setup
| Task | Status | Notes |
|---|---|---|
| S0-T01 Repository and tooling | Partial | Layout, `.gitignore`, `.env.example` done. No pre-commit hooks, Prettier or "fail if .env tracked" CI check yet. |
| S0-T02 Supabase project and local stack | Partial | Local stack works. The hosted project (`hgcvaekiwlbqwcgchjos`) has the migrations and template applied (5 Nov) and the app has been run against it with a real login. |
| S0-T03 Backend skeleton | Done | `/health`, error shape, CORS, settings. Tested. |
| S0-T04 JWT authentication | Done | HS256 (local) tested with real tokens; ES256/JWKS (what your hosted project uses) tested with a generated key, including rejection of a wrong key and of an HS256 downgrade. The live JWKS fetch from your project was confirmed to work. |
| S0-T05 Frontend skeleton | Partial | Vite + React + TS + Tailwind + Router + Query + Vitest work; build and lint pass. Prettier not set up. |
| S0-T06 Auth client + protected routes | Partial | Verified in a real browser (register, login redirect, `/me`). No Playwright test yet. |
| S0-T07 Migration and seed workflow | Partial | Migrations and template seed work and re-apply cleanly. No `seed-test` script (tests create their own users). |
| S0-T08 CI | Partial | `.github/workflows/ci.yml` written; never run (no remote yet). |
| S0-T09 RLS test harness | Done | RLS tested directly through PostgREST as user A, user B and anonymous (`test_api_integration.py`). |
| S0-T10 Deployment (staging) | Partial | Dockerfile, `render.yaml`, `vercel.json` and docs/08-deploy.md are done; the API image was built and run locally. Not deployed yet: needs your Render and Vercel accounts. |

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

## Sprint 2: Dashboard
| Task | Status | Notes |
|---|---|---|
| S2-T01 Scoring service | Done | `services/scoring.py`, pure functions; table-driven tests for every rule and edge case plus a randomised invariant (Done + Missed + N/A + pending = active goal-days). |
| S2-T02 Golden fixture | Done | `tests/golden_winter_arc.py`. Matches the doc for Office before 10 AM (5/9/8/36%); October is 113/99/8/53% because the sheet's marks were corrected after the doc's first draft (doc 05 updated). Cross-checked against a plain tally. |
| S2-T03 Aggregation SQL (RPC) | Skipped | Decision: the maths runs in Python over at most ~5,500 rows (366 x 15); not worth a second implementation to keep in sync. Revisit only if it gets slow. |
| S2-T04 Dashboard endpoint | Partial | `GET /challenges/{id}/dashboard` done and tested (shape, 404 for another user's challenge). No cache yet; it recomputes per request. |
| S2-T05 KPI tiles | Done | Rendered and checked in the browser against the golden data. |
| S2-T06 Per-goal table | Done | Sortable, bar, "retired" tag. |
| S2-T07 Monthly and per-goal-per-month tables | Done | Total rows equal the KPIs (tested); future months hidden. |
| S2-T08 Weekly table and chart | Partial | Table plus CSS bars (decorative; the table is the text alternative). No Recharts and no daily-score line; no axe run. |
| S2-T09 States and responsive layout | Partial | Loading, empty and error states done. Not yet checked at 375px, with throttling or Lighthouse. |

## Sprint 3: Awards and sharing
Tasks whose testing step names Playwright are **Partial**: they have API/integration tests, component tests and a manual two-user
check in a real browser (6 Nov), but no Playwright run yet.

| Task | Status | Notes |
|---|---|---|
| S3-T01 Streaks | Done | `services/streaks.py`; table-driven tests (neutral all-N/A days, today pending, broken then resumed). Dashboard shows current and best streak. |
| S3-T02 Badge catalogue and storage | Done | Migration `20261106000001_awards.sql`, 13 badges seeded. Tested through PostgREST: clients can read their own rows, cannot insert (even for themselves), cannot read others'. |
| S3-T03 Badge engine | Done | `services/badges.py` pure rules, one test per badge just below and at its threshold; integration tests for idempotency and "editing history does not revoke". A day with unlogged goals never earns a badge. |
| S3-T04 Time-based badges | Partial | Halfway / complete / champion are awarded whenever the user opens Awards or stars (catch-up), and by `POST /internal/jobs/awards` (needs `JOB_SECRET`; invisible without it). **Not scheduled yet**: something has to call it nightly (see docs/08-deploy.md). |
| S3-T05 Unlock toast | Partial | `new_badges` in every entry-write response; polite live region, dismissible, auto-hides, tested. No Playwright. |
| S3-T06 Awards page | Done | Earned and locked, "how to earn", filter by challenge. |
| S3-T07 Total stars | Done | `GET /me/stars`, header indicator. |
| S3-T08 Public share links API | Done | 256-bit token, only its SHA-256 stored, shown once, revoke is immediate, owner-only. |
| S3-T09 Public share page | Partial | Unknown, revoked and expired links are byte-identical 404s; nothing identifying leaks (mutation-checked); 30 requests/min per client. Open Graph preview tags are generic: the page is a single-page app, so per-link previews would need server-side rendering. |
| S3-T10 Share link management UI | Partial | Create (scope, expiry), copy, native share sheet, list, revoke. No Playwright. |
| S3-T11 Friend requests API | Done | Same 202 answer for known and unknown emails; you never see requests you sent; duplicates blocked; a request to someone who already asked you is a yes. |
| S3-T12 Friends UI | Partial | List, requests, send by email, remove with confirmation. No Playwright. |
| S3-T13 Share with a friend (API) | Done | 409 unless accepted friends; unshare is immediate; shared-with user can read the share row but not write (RLS tested). |
| S3-T14 Shared-with-me view | Partial | Read-only view, no notes, other challenges invisible; every write route 404s for the viewer (tested). Two-user browser check done by hand. |
| S3-T15 Cascade rules | Done | Unfriending removes shares in both directions; deleting a challenge removes its links and shares. |

## Test inventory
- Backend: 124 passing: unit (dates, auth, scoring, streaks, badges, sharing helpers, dashboard endpoint) plus 16 + 7 + 21 integration tests against local Supabase (sharing, awards, Sprint 1). Integration tests refuse to run against a hosted project.
- Frontend: 53 passing (dates, status control, route guards, API client, dashboard, toasts, awards, sharing panel, friends, shared pages).
- Not yet: Playwright end-to-end, axe accessibility checks, performance checks.

## Known gaps and decisions
- The Python backend uses the service-role key (bypasses RLS), so every repository query is scoped to the caller; RLS stays on as a second layer.
- Multi-step writes (e.g. changing a challenge's dates then realigning goal windows) are separate requests, not one transaction. Fine at this scale; move to a SQL function if it ever matters.
- One integration test (`test_entry_date_rules`) failed once out of about 20 full runs and could not be reproduced. Watch for flakiness.
- "Today" is pending until the day ends in the scoring rules (Sprint 2); the logging screens already use the user's timezone for "today".

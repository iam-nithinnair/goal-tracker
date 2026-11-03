# Sprint 0: Setup

**Goal:** a working skeleton where a logged-in React app calls an authenticated FastAPI endpoint backed by Supabase, with CI green.
**Stories:** enablers (no user story). **Estimate:** about 8d.

### S0-T01 Repository and tooling                                [0.5d]
Description: create the monorepo layout (`frontend/`, `backend/`, `supabase/`, `docs/`, `tasks/`), `.gitignore`, editorconfig, pre-commit hooks (ruff, black, eslint, prettier), `.env.example` files, README run instructions.
Acceptance criteria: fresh clone + README steps starts everything; secrets are git-ignored.
Testing step: clone into a clean folder and follow the README; run `pre-commit run --all-files` (passes). Add a CI check that fails if `.env` is tracked.

### S0-T02 Supabase project and local stack                      [1d]
Description: create dev Supabase project, init Supabase CLI (`supabase/config.toml`), enable local stack, first empty migration, document keys and where each is used.
Acceptance criteria: `supabase start` runs; `supabase db reset` applies migrations cleanly; dev project linked.
Testing step: run `supabase db reset` twice (idempotent); connect with psql and list schemas.

### S0-T03 Backend skeleton (FastAPI)                            [1d]
Description: `app/main.py`, settings via pydantic-settings, `/health`, structured error handler (shape from `04-api.md`), CORS, logging, pytest setup.
Acceptance criteria: `uvicorn` serves `/health` and `/docs`; errors use the documented JSON shape.
Testing step: pytest for `/health`, 404 and validation-error shapes; curl `/health` manually.

### S0-T04 JWT authentication dependency                         [1d]
Description: `get_current_user` verifies Supabase JWT (decide HS256 secret vs JWKS), returns user id and role; `require_role`; `GET /me` stub.
Acceptance criteria: no token = 401; bad/expired token = 401; valid token returns the user id.
Testing step: pytest with generated valid, expired, wrong-audience and tampered tokens; manual call with a real token from the dev project.

### S0-T05 Frontend skeleton (React + Vite + TS)                 [1d]
Description: Vite app, Tailwind, React Router, TanStack Query, ESLint/Prettier, Vitest + RTL, base layout, env handling.
Acceptance criteria: `npm run dev/build/test/lint` all succeed; a placeholder home route renders.
Testing step: Vitest smoke test for the app shell; run the build and open the preview.

### S0-T06 Supabase auth client and protected routes             [1d]
Description: supabase-js client, `AuthProvider`, `ProtectedRoute`, API client that attaches the bearer token and refreshes on 401.
Acceptance criteria: unauthenticated visit redirects to `/login`; after login the app calls `GET /me` successfully.
Testing step: component tests for redirect behaviour; Playwright: log in with a seeded test user and see the `/me` result.

### S0-T07 Migration and seed workflow                           [0.5d]
Description: conventions for migrations, `supabase/seed.sql`, `make seed-test` / script that creates test users and fixture data.
Acceptance criteria: a single command resets the local DB and loads test data.
Testing step: run it twice and verify row counts are identical; documented in README.

### S0-T08 Continuous integration                                [1d]
Description: GitHub Actions: lint + type-check + unit tests (both apps), start local Supabase, run API tests, build frontend, Playwright smoke.
Acceptance criteria: required check on PRs; fails on a deliberate broken test.
Testing step: open a PR with a failing test (CI red), fix it (CI green).

### S0-T09 Test harness for RLS                                  [0.5d]
Description: helper that runs SQL as different roles (anon, user A, user B, service role) for policy tests.
Acceptance criteria: a sample test proves anon cannot select from a placeholder table and user B cannot read user A's row.
Testing step: the sample RLS tests run in CI.

### S0-T10 Deployment (staging)                                  [0.5d]
Description: deploy frontend and backend to staging, set env vars, run migrations from CI.
Acceptance criteria: staging URL loads; login works; `/health` green.
Testing step: run the Playwright smoke test against staging; verify CORS rejects an unknown origin.

## Sprint test pass
- [ ] Fresh clone setup works from README only
- [ ] Sign in on the frontend, `GET /me` returns the user
- [ ] `supabase db reset` + seed works; RLS sample tests pass
- [ ] CI is green on main; staging deployed and smoke test passes

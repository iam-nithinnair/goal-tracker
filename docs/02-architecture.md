# 02 Architecture

## Components
```
 Browser (React SPA)
   |  1. sign in via supabase-js  ---------------------------->  Supabase Auth
   |  <-------------- JWT (access token)
   |
   |  2. REST calls  Authorization: Bearer <JWT>
   v
 FastAPI backend  --- verifies JWT (Supabase JWKS / JWT secret) --->  user id
   |  business logic: scoring, streaks, awards, share tokens
   v
 Supabase Postgres  (RLS on every table)

 Public share page --> FastAPI /public/share/{token}  (no JWT, read-only, scoped by token)
```

## Responsibilities
| Concern | Where |
|---|---|
| Sign-up, login, password reset, sessions | Supabase Auth (client SDK) |
| Identity of every API call | FastAPI dependency that validates the Supabase JWT |
| Validation, scoring, streaks, badges, share tokens | FastAPI services |
| Persistence | Supabase Postgres via the Python Supabase client / asyncpg |
| Isolation between users | API checks ownership **and** RLS policies as a second layer |
| UI state and caching | TanStack Query on the frontend |

## Why a Python backend next to Supabase
Scoring (N/A handling, month/week buckets), streaks and the badge engine are business logic that should be
unit-testable and shared by the dashboard, share pages and award checks. Putting it in one FastAPI service
keeps a single source of truth. The frontend uses supabase-js **only** for auth.

## Repository layout (when build starts)
```
goal-tracker/
  frontend/            React + Vite app
  backend/             FastAPI app (app/, tests/), pyproject.toml
  supabase/            migrations/, seed.sql, config.toml (local stack)
  docs/  tasks/
  .github/workflows/   CI
```

## Backend structure
```
backend/app/
  main.py              app factory, CORS, routers
  core/config.py       settings (pydantic-settings)
  core/auth.py         get_current_user (JWT verify), require_role
  db/                  client + repositories
  routers/             challenges, goals, entries, dashboard, awards, shares, friends (later: groups, admin)
  services/            scoring.py, streaks.py, badges.py, sharing.py
  schemas/             pydantic request/response models
tests/                 unit (services), api (httpx + local Supabase), rls (SQL)
```
`services/scoring.py` is pure functions (no DB) so it can be tested against fixture data copied from the sheet.

## Auth flow
1. Frontend signs in through supabase-js; it stores the session and refreshes tokens.
2. Every API call sends `Authorization: Bearer <access_token>`.
3. FastAPI verifies signature, expiry and audience, extracts `sub` (user id) and role claims.
4. Handlers load only rows where `owner_id = sub` (or a valid share/membership); RLS enforces the same in the database.
5. Public share endpoints take an unguessable token (>= 128 bits, stored hashed) instead of a JWT.

## Configuration (env vars)
| Var | Where | Purpose |
|---|---|---|
| `SUPABASE_URL`, `SUPABASE_ANON_KEY` | frontend | auth client |
| `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET` (or JWKS URL) | backend | DB access and JWT verification |
| `ALLOWED_ORIGINS` | backend | CORS |
| `PUBLIC_APP_URL` | backend | builds share links |
The service-role key lives only on the backend and never in the browser or the repo. `.env.example` files are committed; real `.env` files are git-ignored.

## Environments and deployment
- **Local:** Supabase CLI local stack (`supabase start`), `uvicorn --reload`, `vite dev`.
- **Staging / Production:** separate Supabase projects; frontend on a static host; backend as a container on a small PaaS. Migrations applied by CI via the Supabase CLI.
- **CI (GitHub Actions):** lint + type-check + unit tests (frontend and backend), start local Supabase, run API/RLS tests, build, run Playwright smoke tests. Required on every PR.

## Security
- RLS enabled on all tables; deny by default.
- Rate limiting on auth-adjacent and public-share endpoints.
- Share tokens stored as hashes; revocation is immediate.
- Input validated with pydantic; SQL only through parameterised queries.
- CORS restricted to known origins; secure, httpOnly handling is Supabase's default for the session library in use (document the choice in Sprint 0).
- Audit fields (`created_at`, `updated_at`) on all tables; admin actions logged in Sprint 4.
- Dependency scanning and secret scanning enabled in the repo.

## Decisions to confirm in Sprint 0
1. JWT verification mode (HS256 secret vs asymmetric JWKS) depending on the Supabase project settings.
2. Python DB access: `supabase-py` vs `asyncpg`/SQLAlchemy. Default: **supabase-py** for simple CRUD and SQL functions (RPC) for aggregates; revisit if queries get heavy.
3. Hosting targets and domain.

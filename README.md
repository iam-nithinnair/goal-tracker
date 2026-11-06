# Goal Tracker

Track our own custom challenges and goals.

A web app for running personal goal challenges ("Winter Arc 2026" is the first one). A user signs in,
creates a named challenge with a duration and a list of daily goals, logs each goal as **Yes / No /
Not available** every day, watches a dashboard of completion, earns stars and awards, and shares
achievements with friends. A later sprint adds groups and a super admin.

It replaces the Winter Arc 2026 Google Sheet, whose scoring rules it reproduces exactly
(see `docs/05-scoring-and-awards.md`).

## Stack
| Layer | Choice |
|---|---|
| Frontend | React + TypeScript (Vite), React Router, TanStack Query, Tailwind, Recharts |
| Backend | Python 3.12, FastAPI |
| Data / Auth | Supabase (Postgres + Auth + Row Level Security) |
| Tests | pytest, Vitest + React Testing Library, Playwright, local Supabase for DB/RLS tests |

## Documentation
| Doc | What it covers |
|---|---|
| [01 Product requirements](docs/01-product-requirements.md) | Vision, personas, features, user stories (US-xx) with acceptance criteria, out of scope |
| [02 Architecture](docs/02-architecture.md) | Components, auth flow, deployment, config, security |
| [03 Data model](docs/03-data-model.md) | Tables, relations, RLS policies, indexes |
| [04 API](docs/04-api.md) | REST endpoints, shapes, errors |
| [05 Scoring and awards](docs/05-scoring-and-awards.md) | Formulas from the sheet, streaks, badge catalogue |
| [06 Sprint plan](docs/06-sprint-plan.md) | Sprints, Definition of Ready/Done, testing strategy, risks |
| [07 Hosted Supabase setup](docs/07-hosted-supabase-setup.md) | Connect the app to a hosted Supabase project |
| [08 Deploy](docs/08-deploy.md) | Deploy to Vercel (frontend) and Render (API) |
| [Seed: Winter Arc template](docs/seed/winter-arc-template.md) | Starter challenge and its 10 goals |

## Task lists (one file per sprint)
| Sprint | Theme | File |
|---|---|---|
| 0 | Setup | [sprint-0-setup.md](tasks/sprint-0-setup.md) |
| 1 | Auth, challenges, check-ins | [sprint-1-auth-challenges-checkins.md](tasks/sprint-1-auth-challenges-checkins.md) |
| 2 | Dashboard | [sprint-2-dashboard.md](tasks/sprint-2-dashboard.md) |
| 3 | Awards and sharing | [sprint-3-awards-sharing.md](tasks/sprint-3-awards-sharing.md) |
| 4 | Groups and super admin (later) | [sprint-4-groups-superadmin.md](tasks/sprint-4-groups-superadmin.md) |
| - | Ideas not yet scheduled | [backlog.md](tasks/backlog.md) |

Every task has an ID, acceptance criteria, an estimate and a **testing step**; every sprint ends with a
sprint test pass. A task is not done until its testing step passes.

## Status
Sprints 0 to 3 are built: login, challenges and goals, Yes/No/N/A logging, grid, the dashboard, stars and badges,
public share links, friends and read-only sharing. Sprint 4 (super admin and groups) is next. See
[tasks/STATUS.md](tasks/STATUS.md) for what is done, partial and not started.

## Run it locally
Needs Node 22+, Python 3.12+, Docker (for the local Supabase stack).

```bash
# 1. Database + auth (first run downloads Docker images; applies supabase/migrations)
npx supabase start -x realtime,storage-api,imgproxy,studio,edge-runtime,logflare,vector,supavisor,postgres-meta
npx supabase status -o env        # shows API_URL, ANON_KEY, SERVICE_ROLE_KEY, JWT_SECRET

# 2. Backend  (copy backend/.env.example to backend/.env and fill in the values from step 1)
cd backend
python -m venv .venv && .venv/Scripts/pip install -e ".[dev]"    # Linux/macOS: .venv/bin/pip
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000

# 3. Frontend  (copy frontend/.env.example to frontend/.env.local and fill in the anon key)
cd frontend
npm install
npm run dev                        # http://localhost:5173
```
Sign-up emails (confirmation, password reset) are caught by the local mail inbox at http://127.0.0.1:54324.

## Tests
```bash
cd backend  && .venv/Scripts/python -m pytest tests        # 43 tests; integration ones need `supabase start`
cd frontend && npm test && npm run typecheck && npm run lint && npm run build
```
Integration tests create their own users, so they can be re-run any time. Stop the stack with `npx supabase stop`.

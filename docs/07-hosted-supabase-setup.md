# 07 Connect the app to your hosted Supabase project

Project ref: `hgcvaekiwlbqwcgchjos`
API URL: `https://hgcvaekiwlbqwcgchjos.supabase.co`
Dashboard: https://supabase.com/dashboard/project/hgcvaekiwlbqwcgchjos

What I checked without any credentials: the project signs tokens with **ES256 (asymmetric keys)**, published at
`/auth/v1/.well-known/jwks.json`. The backend already verifies that mode (tests in `backend/tests/test_jwks_auth.py`),
so **leave `SUPABASE_JWT_SECRET` empty** for this project.

Steps 1, 3 and 4 need your account or secret keys, so they are yours to do; nothing here needs to be pasted into chat.

## 1. Create the tables (pick one)
**A. Supabase CLI (recommended, keeps migration history).** From the repo root:
```bash
npx supabase login
npx supabase link --project-ref hgcvaekiwlbqwcgchjos
npx supabase db push
```
`link` and `db push` ask for the **database password** you chose when creating the project (reset it under
Project Settings > Database if you've lost it). `db push` applies, in order:
`20261103000001_core_schema.sql` (tables, row level security, triggers) and
`20261103000002_seed_winter_arc_template.sql` (the Winter Arc template).

**B. No CLI.** Dashboard > SQL Editor > New query. Paste the contents of the two files above, in that order, and run each.

Check: Table Editor shows `profiles`, `challenges`, `goals`, `daily_entries`; `challenges` has one row ("Winter Arc 2026")
and `goals` has 10 rows.

## 2. Auth settings (Dashboard > Authentication)
- **URL Configuration > Site URL:** `http://localhost:5173` while developing (change to your real domain when you deploy).
- **Redirect URLs:** add `http://localhost:5173/**` and `http://127.0.0.1:5173/**` (needed for the password-reset link).
- **Sign In / Providers > Email:** hosted projects require **Confirm email** by default. Leave it on for real use; for
  quick local testing you may turn it off.
- Supabase's built-in email sender is heavily rate-limited (a few emails per hour). Fine for you; add a custom SMTP
  provider before inviting other people.

## 3. Collect the keys (Dashboard > Project Settings > API Keys)
| Value | Goes in | Notes |
|---|---|---|
| Project URL | both | `https://hgcvaekiwlbqwcgchjos.supabase.co` |
| Publishable key (`sb_publishable_...`) or legacy **anon** key | frontend only | safe to ship to browsers |
| Secret key (`sb_secret_...`) or legacy **service_role** key | **backend only** | bypasses row level security. Never put it in the frontend, git or chat |

If the new `sb_...` keys give errors with the Python client, use the legacy keys (API Keys > "Legacy anon, service_role API keys").

## 4. Point the app at it
`backend/.env`:
```
ENVIRONMENT=local
SUPABASE_URL=https://hgcvaekiwlbqwcgchjos.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<secret / service_role key>
SUPABASE_JWT_SECRET=
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```
`frontend/.env.local`:
```
VITE_SUPABASE_URL=https://hgcvaekiwlbqwcgchjos.supabase.co
VITE_SUPABASE_ANON_KEY=<publishable / anon key>
VITE_API_URL=http://127.0.0.1:8000/api/v1
```
Both files are git-ignored. Keep your local-stack values in a copy (e.g. `.env.local-stack`) if you want to switch back.
Restart the API and `npm run dev` after changing them.

## 5. Check it works
1. Open the app, **register** with your real email (confirm it if confirmation is on), create a challenge from the Winter Arc template.
2. In the dashboard, Table Editor > `profiles` should show your row, and `challenges`/`goals` your new challenge.
3. Authentication > Users lists you. Log out and back in; your challenge is still there.

## Safety notes
- **Automated integration tests never run against a hosted project.** They create fake users and data, so
  `backend/tests/conftest.py` skips them unless `SUPABASE_URL` is local (override only with `ALLOW_REMOTE_TESTS=1`, and only
  against a throwaway project). Run them with the local stack: `npx supabase start`, then `pytest`.
- The hosted project holds your real data. Turn on backups (Dashboard > Database > Backups; daily backups need a paid plan,
  otherwise export with `npx supabase db dump`).
- Rotate the secret key if it ever lands in a place it shouldn't (Project Settings > API Keys).
- Deployed frontend and backend (staging/production) are still to do: Sprint 0, task S0-T10.

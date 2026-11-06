# 08 Deploy

Frontend on **Vercel**, backend API on **Render** (Docker), database/auth on your hosted **Supabase** project.
Both hosts deploy straight from the GitHub repo and redeploy on every push to `main`. Both have free tiers.
(Render's free web service sleeps after ~15 minutes idle, so the first request after a pause takes ~30 s.)

Order matters because each side needs the other's URL: backend first, then frontend, then wire them together.

## 1. Backend on Render
1. https://dashboard.render.com > **New > Blueprint** > connect GitHub > pick `iam-nithinnair/goal-tracker`.
   Render reads `render.yaml` and proposes the service `goal-tracker-api`.
2. It asks for the two secret values:
   - `SUPABASE_SERVICE_ROLE_KEY`: your Supabase **secret** (service_role) key.
   - `ALLOWED_ORIGINS`: put `http://localhost:5173` for now; you'll replace it with the Vercel URL in step 3.
3. Deploy. When it's live you get a URL like `https://goal-tracker-api.onrender.com`.
   Check `https://<that-url>/health` returns `{"status":"ok"}`.

## 2. Frontend on Vercel
1. https://vercel.com/new > import `iam-nithinnair/goal-tracker`.
2. **Root Directory:** `frontend`. Framework Vite is detected; `frontend/vercel.json` sets the build and the single-page-app rewrite.
3. **Environment Variables** (these are baked in at build time):
   - `VITE_SUPABASE_URL` = `https://hgcvaekiwlbqwcgchjos.supabase.co`
   - `VITE_SUPABASE_ANON_KEY` = your Supabase **publishable** (anon) key
   - `VITE_API_URL` = `https://<your-render-url>/api/v1`
4. Deploy. You get a URL like `https://goal-tracker-xyz.vercel.app`.

## 3. Wire them together
- **Render > goal-tracker-api > Environment:** set `ALLOWED_ORIGINS` to your Vercel URL (no trailing slash; comma-separate
  extra origins such as a custom domain). Save; it redeploys.
- **Supabase > Authentication > URL Configuration:** set **Site URL** to the Vercel URL and add `https://<vercel-url>/**`
  to **Redirect URLs** (keep the localhost entries for development). Without this, password-reset links won't work.

## 4. Check it
Open the Vercel URL, register, confirm the email if confirmation is on, create a challenge from the Winter Arc template, log a day,
reload. Then Supabase > Table Editor shows your rows.

## 5. Releasing a new sprint
Pushing to `main` redeploys both hosts, but **database changes are not applied automatically**. Before (or right after) pushing a
change that adds a migration, run the new file(s) from `supabase/migrations/` in the hosted project's SQL Editor, oldest first.
Sprint 3 added `20261106000001_awards.sql` and `20261106000002_sharing.sql`. The API tolerates a missing awards table (check-ins
still save; the Awards page shows an error until the SQL is run), but the sharing and friends endpoints need their tables.

## 6. Nightly awards job (optional)
Halfway / challenge complete / champion are awarded whenever someone opens Awards, so nothing is lost without this. To award them
for people who have not opened the app, set `JOB_SECRET` on Render to a long random string and have something call, once a night:

```
curl -X POST https://<render-url>/api/v1/internal/jobs/awards -H "X-Job-Secret: <the secret>"
```

(a Render cron job, or a scheduled GitHub Action with the secret stored as a repository secret). Without `JOB_SECRET` the route
does not exist as far as callers can tell.

## Notes
- The public share endpoint is rate limited in memory (30 requests a minute per client address). That is right for one instance;
  scaling out would need a shared store. Behind Render's proxy the address seen is the proxy's, so the limit is effectively shared.
- The service_role/secret key lives **only** in Render's environment, never in the repo or the frontend.
- `ENVIRONMENT=production` hides `/docs` and `/openapi.json`.
- `backend/requirements.txt` mirrors `[project].dependencies` in `pyproject.toml`; update both when adding a dependency.
- The Docker image was built and run locally to check: health, docs hidden, 401 without a token, CORS allows only `ALLOWED_ORIGINS`, runs as a non-root user.
- Secure by default, still to do before inviting others: custom SMTP for auth emails, a custom domain, error monitoring, backups.

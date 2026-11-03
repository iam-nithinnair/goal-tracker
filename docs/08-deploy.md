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

## Notes
- The service_role/secret key lives **only** in Render's environment, never in the repo or the frontend.
- `ENVIRONMENT=production` hides `/docs` and `/openapi.json`.
- `backend/requirements.txt` mirrors `[project].dependencies` in `pyproject.toml`; update both when adding a dependency.
- The Docker image was built and run locally to check: health, docs hidden, 401 without a token, CORS allows only `ALLOWED_ORIGINS`, runs as a non-root user.
- Secure by default, still to do before inviting others: custom SMTP for auth emails, a custom domain, error monitoring, backups.

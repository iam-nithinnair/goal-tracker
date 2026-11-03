# 04 API

REST + JSON, served by FastAPI under `/api/v1`. All endpoints except `/public/*` and `/health` require
`Authorization: Bearer <Supabase JWT>`. Interactive docs at `/docs` (OpenAPI) in non-production.

## Conventions
- Dates are ISO `YYYY-MM-DD`; timestamps are ISO 8601 UTC.
- Status values: `yes | no | na`.
- Errors: `{ "error": { "code": "validation_error", "message": "...", "fields": {...} } }`
  with HTTP 400 (validation), 401 (no/invalid token), 403 (not allowed), 404 (not found or not yours), 409 (conflict), 429 (rate limit).
- Resources that belong to someone else return **404**, not 403, so existence is not leaked.
- Lists accept `limit` and `cursor` where they can grow.

## Health
- `GET /health` returns `{ "status": "ok" }`.

## Me
- `GET /me` returns profile `{ id, display_name, avatar_color, timezone, role }`.
- `PATCH /me` updates `display_name`, `avatar_color`, `timezone`.

## Templates
- `GET /templates` lists system templates `[{ id, name, goals: [...] }]`.

## Challenges
- `GET /challenges` lists my challenges (with `status`, dates).
- `POST /challenges` body `{ name, start_date, end_date, template_id? , goals?: [{name}] }`.
- `GET /challenges/{id}` returns the challenge with its goals.
- `PATCH /challenges/{id}` updates `name`, `start_date`, `end_date`, `status`.
- `DELETE /challenges/{id}` deletes (requires `?confirm=true`).

## Goals
- `POST /challenges/{id}/goals` body `{ name, position? }`.
- `PATCH /goals/{goal_id}` body `{ name?, position? }`.
- `PUT /challenges/{id}/goals/order` body `{ goal_ids: [...] }` sets the order; must list every goal of the challenge exactly once.
- `POST /goals/{goal_id}/retire` body `{ on: date }` sets `active_to` (the last day the goal counts).
- `DELETE /goals/{goal_id}?confirm=true` removes the goal and its entries.

## Entries (check-ins)
- `GET /challenges/{id}/entries?from=&to=` returns `{ date, goal_id, status }[]` for the range.
- `PUT /goals/{goal_id}/entries/{date}` body `{ status }` upserts one entry (idempotent).
- `PUT /challenges/{id}/entries/{date}` body `{ entries: [{ goal_id, status }] }` upserts a whole day.
- `DELETE /goals/{goal_id}/entries/{date}` clears an entry (back to "not logged").
- Rejects future dates (in the user's timezone) and dates outside the challenge or the goal's active window with 400.

## Dashboard (computed by the scoring service)
- `GET /challenges/{id}/dashboard` returns:
  ```json
  {
    "as_of": "2026-10-27",
    "kpis": { "days_in": 22, "days_left": 65, "overall_completion": 0.52,
              "perfect_days": 0, "goals_completed": 110 },
    "goals": [ { "goal_id": "...", "name": "Office before 10 AM",
                 "done": 5, "missed": 9, "na": 8, "completion": 0.36 } ],
    "months": [ { "month": "2026-10", "days": 22, "done": 110, "missed": 102, "na": 8,
                  "completion": 0.52, "perfect_days": 0, "avg_daily_score": 0.51, "best_day": 0.90 } ],
    "goal_months": [ { "goal_id": "...", "month": "2026-10", "done": 5, "missed": 9, "na": 8, "completion": 0.36 } ],
    "weeks": [ { "week": 1, "from": "2026-10-06", "to": "2026-10-12", "done": 43, "possible": 68, "completion": 0.63 } ],
    "days": [ { "date": "2026-10-06", "done": 9, "applicable": 10, "score": 0.9 } ]
  }
  ```
- `GET /challenges/{id}/dashboard/export?format=csv` downloads the grid (backlog candidate).

## Awards
- `GET /badges` lists the catalogue with my earned status: `[{ code, name, description, stars, earned_on? }]`.
- `GET /me/stars` returns `{ total_stars, by_challenge: [...] }`.
- Awards are evaluated server side after each entry write; the write response includes `new_badges: []` so the UI can toast them.

## Sharing: public links
- `POST /challenges/{id}/share-links` body `{ scope, expires_at? }` returns `{ id, url }`. The token appears **only** in this response.
- `GET /challenges/{id}/share-links` lists links (no tokens): `{ id, scope, created_at, expires_at, revoked_at }`.
- `DELETE /share-links/{id}` revokes.
- `GET /public/share/{token}` (no auth, rate limited) returns `{ display_name, challenge_name, dates, completion, streak, stars, badges, dashboard? }`
  depending on scope. Never returns email, notes, other challenges or ids that allow further lookups.

## Sharing: friends
- `GET /friends` lists accepted friends and pending requests.
- `POST /friends/requests` body `{ email }` sends a request (response never reveals whether the email has an account).
- `POST /friends/requests/{id}/accept` and `/decline`.
- `DELETE /friends/{user_id}` removes a friend (also removes any challenge shares between the two).
- `POST /challenges/{id}/shares` body `{ friend_id }` shares with a friend (409 if not friends).
- `DELETE /challenges/{id}/shares/{friend_id}` unshares.
- `GET /shared-with-me` lists challenges friends shared with me.
- `GET /shared-with-me/{challenge_id}/dashboard` returns the dashboard, read-only.

## Sprint 4 (later)
- Admin (`super_admin` only): `GET /admin/users`, `PATCH /admin/users/{id}` (disable/enable), `GET /admin/challenges`, `GET/POST/PATCH /admin/badges`.
- Groups: `POST /groups`, `GET /groups`, `GET /groups/{id}`, `POST /groups/{id}/members` (invite/add), `PATCH /groups/{id}/members/{user_id}` (role),
  `DELETE /groups/{id}/members/{user_id}`, `POST /groups/{id}/challenges`, `GET /groups/{id}/leaderboard`, `GET /groups/{id}/dashboard`.

## Security notes
Ownership is checked in every handler and again by RLS. Public endpoints are rate limited and return identical responses for
unknown, revoked and expired tokens (404).

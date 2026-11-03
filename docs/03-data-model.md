# 03 Data model

Postgres on Supabase. All tables have `id uuid primary key default gen_random_uuid()`, `created_at`
and `updated_at timestamptz`. Users live in Supabase's `auth.users`; `profiles` extends them.

## Entity overview
```
auth.users 1--1 profiles
profiles 1--* challenges 1--* goals 1--* daily_entries
profiles *--* badges           (user_badges)
challenges 1--* share_links
profiles *--* profiles         (friendships)
challenges *--* profiles       (challenge_shares)
-- sprint 4:
profiles 1--* groups 1--* group_members *--1 profiles
groups 1--* group_challenges *--1 challenges
```

## MVP tables

### profiles
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | = `auth.users.id` |
| display_name | text | 1-50 chars |
| avatar_color | text | |
| timezone | text | IANA name, default `UTC`; defines "today" |
| role | text | `user` (default) or `super_admin` (used from sprint 4) |
| is_disabled | bool | default false (sprint 4) |

### challenges
| Column | Type | Notes |
|---|---|---|
| owner_id | uuid FK profiles | |
| name | text | 1-80 chars |
| start_date, end_date | date | `end_date >= start_date`, max 366 days |
| status | text | `active`, `archived` |
| is_template | bool | system templates (e.g. Winter Arc) have `owner_id` null and are read-only |

### goals
| Column | Type | Notes |
|---|---|---|
| challenge_id | uuid FK | on delete cascade |
| name | text | 1-80 chars |
| position | int | display order |
| active_from | date | default challenge start |
| active_to | date null | null = active to the end; set when a goal is retired (inclusive) |

A goal counts in scoring only on dates between `active_from` and `active_to` (this is how "Meditate" is removed from
November without touching October).

### daily_entries
| Column | Type | Notes |
|---|---|---|
| goal_id | uuid FK | on delete cascade |
| entry_date | date | must lie within the challenge and not be in the future (in the owner's timezone) |
| status | text | `yes`, `no`, `na` |
| UNIQUE (goal_id, entry_date) | | upsert on write |

No row means "not logged": counted as No for past days, ignored for today and future (see scoring doc).

### badges (catalogue)
`code` (unique, e.g. `FIRST_PERFECT_DAY`), `name`, `description`, `stars int`, `rule jsonb`, `is_active`.

### user_badges
`user_id`, `badge_id`, `challenge_id null`, `earned_on date`. UNIQUE (user_id, badge_id, challenge_id).

### share_links (public, no account needed)
| Column | Type | Notes |
|---|---|---|
| challenge_id | uuid FK | |
| token_hash | text unique | SHA-256 of the random token; the token itself is shown once |
| scope | text | `achievements` (card only) or `dashboard` |
| expires_at | timestamptz null | |
| revoked_at | timestamptz null | |

### friendships
`requester_id`, `addressee_id`, `status` (`pending|accepted|declined`). One row per pair (unique on the ordered pair);
check `requester_id <> addressee_id`.

### challenge_shares (in-app sharing to a friend)
`challenge_id`, `shared_with_id`, `created_at`. UNIQUE (challenge_id, shared_with_id). The API only allows it when an
accepted friendship exists.

## Sprint 4 tables
- **groups**: `name`, `owner_id`.
- **group_members**: `group_id`, `user_id`, `role` (`owner|member`), `status` (`invited|active`). UNIQUE (group_id, user_id).
- **group_challenges**: `group_id`, `template_challenge_id` (the owner's definition of name, dates, goals). Each member gets
  their own `challenges` row cloned from it (linked by `group_challenge_id` on `challenges`) so entries stay personal.
- **admin_audit_log**: `actor_id`, `action`, `target`, `details jsonb`.

## Row Level Security (summary)
| Table | Policy |
|---|---|
| profiles | select/update own row; select display_name of friends and of members sharing a group |
| challenges | owner: full access. Shared-with user: select. Templates: select by all authenticated. |
| goals, daily_entries | owner: full access via challenge ownership. Shared-with user: select only. |
| user_badges | select own; insert only by backend (service role) |
| share_links | owner only; public reads go through the API (service role), not direct table access |
| friendships | select where requester or addressee; insert as requester; update status as addressee |
| challenge_shares | owner insert/delete/select; shared-with select |
| super_admin (sprint 4) | additional read policies keyed on `profiles.role = 'super_admin'` |
Default: RLS enabled everywhere, no policy = no access.

## Indexes
- `challenges (owner_id)`, `goals (challenge_id, position)`
- `daily_entries (goal_id, entry_date)` (unique) and `(entry_date)` for range scans
- `share_links (token_hash)` unique, `friendships (addressee_id, status)`

## Database functions (RPC)
- `dashboard_counts(challenge_id, as_of date)` returns per-goal, per-month and per-day aggregates used by the scoring service
  (keeps heavy counting in SQL; the percentage maths stays in Python for testability).

## Migrations
SQL files under `supabase/migrations/`, one per change, applied by the Supabase CLI locally and in CI. A seed file inserts
the Winter Arc template challenge (see `docs/seed/winter-arc-template.md`).

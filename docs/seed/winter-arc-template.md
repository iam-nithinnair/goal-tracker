# Seed: Winter Arc template

A system template (`challenges.is_template = true`, no owner) that users can copy when creating a challenge.
It contains **goals only, no daily values**. The first user will enter their own values after signing up.

- **Name:** Winter Arc 2026
- **Suggested dates:** 6 Oct 2026 to 31 Dec 2026 (87 days). When copied, the user can change both dates.

## Goals (in order)
| # | Goal |
|---|---|
| 1 | Wake up 8 AM |
| 2 | Cold shower |
| 3 | Office before 10 AM |
| 4 | In bed before 12 AM |
| 5 | Cut sugar |
| 6 | Cut oily & junk food |
| 7 | Drink 3 L water |
| 8 | Walk 5k steps |
| 9 | Read 10 min |
| 10 | Workout 30 min |

Meditate (10 min) was part of the original sheet in October and removed from November; it is **not** in the template. A user who wants it
can add it as a goal (or add it and retire it later to see how retiring works).

## Seed SQL (outline for Sprint 1)
```sql
insert into challenges (id, owner_id, name, start_date, end_date, is_template)
values ('<fixed uuid>', null, 'Winter Arc 2026', '2026-10-06', '2026-12-31', true);
insert into goals (challenge_id, name, position) values
  ('<fixed uuid>', 'Wake up 8 AM', 1), ('<fixed uuid>', 'Cold shower', 2), ...;
```
The template is read-only to everyone (RLS select only); copying it clones the challenge and goals under the caller's ownership.

## Not imported
The existing Google Sheet's Oct-Nov values are **not** imported. A CSV/sheet import is in `tasks/backlog.md` if wanted later.

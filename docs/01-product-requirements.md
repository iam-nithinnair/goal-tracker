# 01 Product requirements

## Vision
Make it easy to commit to a time-boxed personal challenge, log it in seconds each day, and see honestly
how it is going, with enough encouragement (stars, awards, a friend watching) to keep going.

## Personas
- **Challenger** (primary): runs one or more challenges, logs daily, wants a clear dashboard.
- **Friend** (secondary): receives a share link or a share in-app; read-only view of someone's progress.
- **Group member / group owner** (later sprint): works on shared goals with others.
- **Super admin** (later sprint): manages users, challenges and the badge catalogue.

## Core concepts
- **Challenge**: a name, a start date and an end date, owned by one user.
- **Goal**: a daily item inside a challenge (e.g. "Cold shower"). A goal can be retired part-way
  through (like Meditate in the sheet) without losing history.
- **Entry**: one goal on one date with status **Yes**, **No** or **Not available** (N/A).
  No entry on a past day counts as No.
- **Star / award (badge)**: recognition earned automatically from entries.
- **Share**: a public read-only link, or sharing a challenge with a registered friend.

## Scope by release
| Release | Included |
|---|---|
| MVP (sprints 0-3) | Login, challenges and goals, Yes/No/N/A logging, dashboard, stars and awards, sharing (public link + friend) |
| Later (sprint 4) | Super admin, groups, group challenges and leaderboard |
| Not now | See "Out of scope" and `tasks/backlog.md` |

## User stories and acceptance criteria

### Accounts
- **US-01 Sign up / log in.** As a user I can register and log in with email and password (magic link as an alternative) so my data is private to me.
  - Given a new email, when I register and confirm, then I land on my (empty) home screen.
  - Wrong credentials show a clear error and never reveal whether the email exists.
  - Logging out ends the session on that device.
- **US-02 Reset password.** I can request a reset email and set a new password.
- **US-03 Profile.** I can set a display name and avatar colour; the name appears on shared pages.

### Challenges and goals
- **US-04 Create a challenge.** I can create a challenge with a name, start date and end date.
  - End date must be on or after start date; maximum length 366 days.
  - Names are 1-80 characters.
- **US-05 Start from a template.** I can start from the "Winter Arc" template (10 goals, no values) and edit it.
- **US-06 Manage goals.** I can add, rename, reorder and retire goals.
  - Retiring a goal on a date keeps all earlier entries and excludes the goal from scoring after that date.
  - Deleting a goal that has entries asks for confirmation and warns that history is lost; retiring is the recommended path.
- **US-07 Edit/end a challenge.** I can change the name, extend or shorten the dates (not before the first logged entry), archive or delete it.

### Daily logging
- **US-08 Log today.** On my home screen I see today's goals and set each to Yes / No / Not available with one tap.
  - Status can be changed any time; the last value wins.
- **US-09 Backfill.** I can pick any past date inside the challenge and log it. I cannot log future dates.
- **US-10 Check-in grid.** I see a date-by-goal grid for the challenge (like the sheet) and can edit cells in it.

### Dashboard
- **US-11 Overview.** I see days in, days left, overall completion %, perfect days and total goals completed.
- **US-12 Per goal.** I see done / missed / N/A / completion % for each goal.
- **US-13 Monthly.** I see a monthly summary (days, done, missed, N/A, completion %, perfect days, average daily score, best day) and a per-goal-per-month table.
- **US-14 Weekly.** I see goals hit vs possible per week and a weekly chart.
- Numbers follow `05-scoring-and-awards.md` exactly.

### Stars and awards
- **US-15 Earn awards.** I automatically earn badges (e.g. First perfect day, 7-day streak, 80% month, Challenge complete) and see a toast when one unlocks.
- **US-16 Awards page.** I see earned badges (with date) and locked ones (with how to earn them), plus my total stars.

### Sharing
- **US-17 Public link.** I can create a read-only link to an achievement card for a challenge (name, completion %, streak, badges); I can revoke it any time; it can have an optional expiry.
  - The page needs no login and never exposes email, other challenges or notes.
- **US-18 Friends.** I can send a friend request by email, accept or decline requests, and remove friends.
- **US-19 Share to a friend.** I can share a challenge with an accepted friend, who then sees my dashboard read-only inside their app. I can unshare.

### Groups and admin (later)
- **US-20 Super admin console.** A super admin can list users, disable accounts, view all challenges, and manage the badge catalogue.
- **US-21 Groups.** I can create a group, invite or add people, and assign roles (owner, member).
- **US-22 Group challenge.** A group owner defines a challenge and goals; each member logs their own entries; the group sees a leaderboard and group completion %.

## Non-functional requirements
- **Privacy:** a user can only read/write their own data (enforced in the API and by Row Level Security). Shared views are read-only and scoped.
- **Performance:** dashboard for a 366-day, 15-goal challenge loads in under 1 second (computed server side, cached per challenge).
- **Accessibility:** WCAG 2.1 AA for core flows; status is never conveyed by colour alone (✓ / ✗ / N/A text or icon too).
- **Responsive:** logging works well one-handed on a phone; the dashboard degrades gracefully.
- **Timezone:** "today" is the user's profile timezone, not the server's.
- **Reliability:** logging a status is idempotent; offline/retry behaviour is in the backlog.

## Out of scope (for now)
Push/email reminders, offline/PWA, numeric metrics (water litres, steps, sleep hours) and notes per day,
native mobile apps, social feed/comments, payments. See `tasks/backlog.md`.

## Open questions
1. Should friends also be able to cheer (react) on shared progress? (Backlog candidate.)
2. Should a perfect day require 100% of applicable goals, or allow a configurable threshold? (Defaulting to 100%, as in the sheet.)
3. Hosting target for frontend and backend (affects Sprint 0 CI/CD). Suggested: Vercel/Netlify for the frontend, Render/Fly.io/Railway for FastAPI.

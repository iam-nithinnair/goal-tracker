# Sprint 1: Auth, challenges, check-ins

**Goal:** a user can sign up, create a challenge (from the Winter Arc template or from scratch) and log Yes / No / Not available.
**Stories:** US-01 to US-10. **Estimate:** about 12d. Depends on Sprint 0.

### S1-T01 Sign-up and log-in screens                              [1.5d]
Description: email/password registration and login (magic link optional), form validation, error states, loading states. Creates a `profiles` row on first sign-up (DB trigger or API).
Acceptance criteria: US-01: valid registration lands on home; wrong password shows a generic error; no account enumeration.
Testing step: RTL tests for validation and error messages; Playwright: register a new user, log out, log in; pytest/SQL: profile row exists after sign-up.

### S1-T02 Session handling and logout                             [0.5d]
Description: persist session, refresh token, logout on all tabs, protected routes everywhere.
Acceptance criteria: reload keeps me signed in; logout clears the session and returns to `/login`.
Testing step: Playwright: log in, reload, still in; log out, back button does not reveal data.

### S1-T03 Password reset                                          [0.5d]
Description: request reset email, set new password screen.
Acceptance criteria: US-02: reset flow completes and the old password stops working.
Testing step: Playwright with the local Supabase inbox (Inbucket): request reset, follow link, set password, log in with the new one.

### S1-T04 Profile settings                                        [0.5d]
Description: `GET/PATCH /me`, settings screen for display name, avatar colour, timezone (default from browser).
Acceptance criteria: US-03: changes persist; name 1-50 chars; invalid timezone rejected.
Testing step: pytest for validation and persistence; RTL for the form; manual check that a change shows on reload.

### S1-T05 Create a challenge                                      [1d]
Description: tables (`challenges`, `goals`, `daily_entries`) + RLS migration; `POST /challenges`, `GET /challenges`; creation form (name, start, end).
Acceptance criteria: US-04: name 1-80 chars, end >= start, max 366 days; the challenge appears in my list.
Testing step: pytest for each validation rule; RLS test: user B cannot list or read user A's challenge; Playwright create flow.

### S1-T06 Winter Arc template                                     [0.5d]
Description: seed the template (see `docs/seed/winter-arc-template.md`); `GET /templates`; "Start from Winter Arc" option copies goals only.
Acceptance criteria: US-05: new challenge has the 10 goals, no entries; editing the copy never changes the template.
Testing step: pytest: copy then edit, template unchanged; RLS: template is read-only for everyone; Playwright flow.

### S1-T07 Add, rename and reorder goals                           [1.5d]
Description: goal endpoints and UI (inline add, rename, drag-and-drop or up/down reorder).
Acceptance criteria: US-06: order persists; names 1-80 chars; duplicate names allowed but warned.
Testing step: pytest for create/update/reorder and ownership (404 for another user's goal); RTL for reorder; manual drag test on a phone-width viewport.

### S1-T08 Retire and delete goals                                 [1d]
Description: `POST /goals/{id}/retire` sets `active_to`; delete with confirmation; UI explains the difference.
Acceptance criteria: US-06: retired goal stays in history, hidden from today's list after the date; delete requires confirmation and removes entries.
Testing step: pytest: retire on a date, entries before/after behave per `05-scoring-and-awards.md`; delete without `confirm=true` is rejected; Playwright flow.

### S1-T09 Edit, archive and delete a challenge                    [1d]
Description: edit name/dates (dates cannot exclude logged entries), archive, delete with confirmation.
Acceptance criteria: US-07: shortening below the last logged entry is rejected with a clear message; archived challenges are hidden from the active list but viewable.
Testing step: pytest for each rule; RLS check on delete; Playwright for archive and restore.

### S1-T10 Log today (Yes / No / Not available)                    [1.5d]
Description: home screen lists today's active goals with a three-state control; `PUT /goals/{id}/entries/{date}`; optimistic update; "today" uses the profile timezone.
Acceptance criteria: US-08: one tap sets the status; last value wins; status shown with text/icon, not colour only; works one-handed at 375px.
Testing step: pytest: upsert idempotency and last-write-wins, future date rejected, timezone edge (23:30 vs 00:30 local); RTL for the control with keyboard and screen-reader labels; Playwright on a mobile viewport.

### S1-T11 Backfill past days                                      [1d]
Description: date picker/day navigation limited to the challenge dates and the goal's active window; batch `PUT /challenges/{id}/entries/{date}`.
Acceptance criteria: US-09: past days editable, future days blocked; dates outside the challenge blocked.
Testing step: pytest for boundary dates (first day, last day, today+1, before start); Playwright: log three past days and reload.

### S1-T12 Check-in grid                                           [1.5d]
Description: date-by-goal grid (like the sheet) with sticky headers, inline editing via the same control, month grouping, scroll to today.
Acceptance criteria: US-10: matches data from `GET /challenges/{id}/entries`; editing a cell saves; handles 366 x 15 smoothly.
Testing step: RTL for cell editing; performance check with a generated 366 x 15 dataset (renders under 1s); Playwright edit and reload.

### S1-T13 Data isolation tests                                    [0.5d]
Description: dedicated suite proving user A's data is invisible and unwritable to user B and anonymous callers across every Sprint 1 table and endpoint.
Acceptance criteria: all cross-user attempts return 404 (API) or no rows (RLS).
Testing step: this task is the test suite; it runs in CI and must stay green.

## Sprint test pass
- [ ] Sign up a new user, log out, log in again
- [ ] Create a challenge from the Winter Arc template; edit goals (add, rename, reorder, retire one)
- [ ] Log Yes / No / N/A for today and 3 past days; reload; values persist
- [ ] Grid view shows the same values; editing there works
- [ ] A second user cannot see any of it (UI, API and direct DB)
- [ ] Phone-width layout checked; keyboard-only logging works; axe reports no serious violations

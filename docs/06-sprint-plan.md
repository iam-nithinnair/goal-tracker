# 06 Sprint plan

## Cadence and assumptions
- 2-week sprints, one developer (can be split across more). Estimates in ideal days (d); total per sprint is a guide, not a promise.
- MVP = sprints 0-3 (about 8 weeks). Sprint 4 (groups, super admin) is a later release.
- Scope is driven by user stories US-xx in `01-product-requirements.md`.

## Roadmap
| Sprint | Goal | Stories | Task file |
|---|---|---|---|
| 0 | Working skeleton: repo, Supabase, FastAPI, React, CI | (enablers) | [sprint-0](../tasks/sprint-0-setup.md) |
| 1 | A user can sign up, create a challenge with goals, and log Yes/No/N/A | US-01..10 | [sprint-1](../tasks/sprint-1-auth-challenges-checkins.md) |
| 2 | Dashboard that matches the Winter Arc sheet | US-11..14 | [sprint-2](../tasks/sprint-2-dashboard.md) |
| 3 | Stars/awards and sharing (public link + friends) | US-15..19 | [sprint-3](../tasks/sprint-3-awards-sharing.md) |
| 4 (later) | Super admin and groups | US-20..22 | [sprint-4](../tasks/sprint-4-groups-superadmin.md) |

## Story-to-task coverage
| Story | Tasks |
|---|---|
| US-01 Sign up/log in | S1-T01, S1-T02 |
| US-02 Reset password | S1-T03 |
| US-03 Profile | S1-T04 |
| US-04 Create challenge | S1-T05 |
| US-05 Template | S1-T06 |
| US-06 Manage goals | S1-T07, S1-T08 |
| US-07 Edit/end challenge | S1-T09 |
| US-08 Log today | S1-T10 |
| US-09 Backfill | S1-T11 |
| US-10 Grid | S1-T12 |
| US-11..14 Dashboard | S2-T01..T09 |
| US-15, US-16 Awards | S3-T01..T07 |
| US-17 Public link | S3-T08..T10 |
| US-18, US-19 Friends | S3-T11..T15 |
| US-20 Admin | S4-T01..T04 |
| US-21, US-22 Groups | S4-T05..T11 |

## Task template (used in every sprint file)
```
### S<n>-T<nn> Title                                  [estimate]
Description: what and why.
Acceptance criteria: observable conditions.
Testing step: automated tests to add + a manual check with expected result.
```

## Definition of Ready
A task is ready when its story and acceptance criteria are clear, its API/data changes are in the docs, and its testing step is written.

## Definition of Done
- Code merged to main through a reviewed PR; CI is green.
- **Testing step passed**: the task's automated tests are written and passing, and its manual check was run.
- Acceptance criteria demonstrated; docs (`03`, `04`, `05`) updated if the task changed data, API or rules.
- No new lint, type or accessibility violations; no secrets committed.
- RLS policy and ownership checks covered by a test if the task touches user data.
- Sprint closes only after the **sprint test pass** at the end of its task file succeeds.

## Testing strategy
| Level | Tools | What it covers | Where it runs |
|---|---|---|---|
| Unit (backend) | pytest | scoring, streaks, badge rules (pure functions, fixture data from the sheet) | every PR |
| API (backend) | pytest + httpx against local Supabase | endpoints, validation, ownership (404 on others' data), error shape | every PR |
| Database / RLS | pgTAP or SQL scripts through pytest, local Supabase | every policy: owner, other user, friend, anonymous | every PR |
| Unit/component (frontend) | Vitest + React Testing Library | forms, status picker, dashboard components | every PR |
| End to end | Playwright against local stack | sign up -> create -> log -> dashboard -> share | every PR (smoke), nightly (full) |
| Accessibility | axe in Playwright/RTL | core screens, status not colour-only | every PR |
| Manual exploratory | checklist per sprint | phone layout, copy, edge cases | sprint end |
Test data: a `make seed-test` script creates users and a challenge with fixture entries; the sheet-derived dataset (docs/05) is the golden fixture for scoring.
Coverage target: >= 90% on `services/`, >= 70% overall; reviewers check the testing step, not just the percentage.

## Risks
| Risk | Mitigation |
|---|---|
| Scoring differs from the sheet and erodes trust | Golden fixture from the sheet; scoring is pure functions with exhaustive tests |
| Data leaks between users | RLS + ownership checks + dedicated tests for other-user and anonymous access |
| Public share links abused or guessed | 128-bit tokens, hashed storage, revoke, expiry, rate limiting, uniform 404 |
| Timezone bugs ("today" off by one) | Store dates, not timestamps, for entries; compute today from profile timezone; tests across timezones |
| Python/Supabase integration friction | Decide JWT mode and DB client in Sprint 0 with a thin vertical slice |
| Scope creep (metrics, reminders) | Park in backlog; revisit after MVP |

## Release checklist (MVP)
All sprint test passes green; production Supabase project with migrations applied; env vars set; backups enabled; privacy page and
terms stub; error monitoring; smoke test run against production.

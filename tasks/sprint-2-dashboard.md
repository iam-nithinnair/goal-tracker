# Sprint 2: Dashboard

**Goal:** a dashboard whose numbers match the Winter Arc sheet. **Stories:** US-11 to US-14. **Estimate:** about 10d. Depends on Sprint 1.

### S2-T01 Scoring service (pure functions)                        [2d]
Description: `services/scoring.py` implementing the rules in `docs/05-scoring-and-awards.md`: effective status, per-goal, per-day, weekly, monthly, per-goal-per-month, KPIs. No DB access.
Acceptance criteria: all formulas and edge cases in doc 05 are implemented (retired goals, N/A, pending today, not started, ended).
Testing step: pytest table-driven unit tests per rule and edge case; property test that Done + Missed + N/A + Pending equals active goal-days.

### S2-T02 Golden fixture from the sheet                           [1d]
Description: build a fixture dataset of the Winter Arc challenge (6 Oct to 27 Oct, 10 goals, the N/A days) and expected outputs.
Acceptance criteria: fixture reproduces Office before 10 AM = 5 done / 9 missed / 8 N/A / 36%, October = 113 / 99 / 8 / 53%, best day 90%, average daily score 53% (the sheet's marks as imported; see doc 05).
Testing step: pytest asserts every expected number; the fixture file is documented so a change to it needs review.

### S2-T03 Aggregation SQL (RPC)                                   [1d]
Description: `dashboard_counts(challenge_id, as_of)` returning per-goal, per-month and per-day counts; indexes verified.
Acceptance criteria: output equals the pure-Python computation on the golden fixture; runs under 300 ms for 366 x 15.
Testing step: pytest compares RPC output with the service on fixtures; EXPLAIN check and timing on a generated large dataset.

### S2-T04 Dashboard endpoint                                      [1d]
Description: `GET /challenges/{id}/dashboard` as in `04-api.md`; ownership enforced; short cache keyed by last entry write.
Acceptance criteria: response shape matches the doc; another user's challenge returns 404; cache invalidates after an entry write.
Testing step: pytest for shape, ownership and cache invalidation; schema test against the OpenAPI spec.

### S2-T05 KPI tiles                                               [0.5d]
Description: days in, days left, overall completion, perfect days, goals completed.
Acceptance criteria: US-11: values match the API; "-" when the challenge has not started.
Testing step: RTL with mocked responses (normal, not started, ended); manual compare against the golden fixture in the UI.

### S2-T06 Per-goal table                                          [1d]
Description: Goal, Done, Missed, N/A, Completion with sorting and a bar.
Acceptance criteria: US-12: retired goals are shown with a "retired" tag and stop accumulating.
Testing step: RTL for sorting and the retired tag; compare numbers to the golden fixture.

### S2-T07 Monthly summary and per-goal-per-month tables          [1.5d]
Description: monthly summary (days, done, missed, N/A, completion, perfect days, average daily score, best day, total row) and per-goal-per-month tables.
Acceptance criteria: US-13: months outside the challenge or in the future show "-"; totals equal the overall KPIs.
Testing step: RTL snapshot with fixture data; test that the total row equals the sum of the months; manual check against the sheet screenshot.

### S2-T08 Weekly table and charts                                 [1d]
Description: weekly table (goals hit, possible, %) and charts (weekly completion bars, optional daily score line) with Recharts.
Acceptance criteria: US-14: week 1 starts on the challenge start; last week handles partial length; charts have text alternatives.
Testing step: RTL for chart data mapping; unit test for partial last week; axe check.

### S2-T09 States, performance and responsive layout              [1d]
Description: loading skeletons, empty state ("log your first day"), error state, mobile layout.
Acceptance criteria: dashboard loads under 1s on the large fixture; usable at 375px.
Testing step: Playwright with network throttling and the large dataset; Lighthouse accessibility >= 90.

## Sprint test pass
- [ ] Golden fixture numbers appear exactly in the UI
- [ ] Change an entry; dashboard updates on refresh (and after cache invalidation)
- [ ] Mark a day N/A; denominators change as documented
- [ ] Retire a goal; history intact and counts stop after the retire date
- [ ] Another user's dashboard returns 404
- [ ] Mobile layout and accessibility checks pass

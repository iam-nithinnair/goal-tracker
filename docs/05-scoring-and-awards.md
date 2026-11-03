# 05 Scoring and awards

These rules are lifted from the Winter Arc 2026 Google Sheet so the app reproduces the same numbers.

## Definitions
For a challenge, an **as-of date** `T` = min(today in the user's timezone, challenge end date).

- **Elapsed days** = days from the challenge start through `T` inclusive (0 if the challenge has not started).
- A goal is **active on a day** if `active_from <= day <= active_to` (or `active_to` is null).
- For each active (goal, day) up to `T` the **effective status** is:
  - `yes` -> Done
  - `no` -> Missed
  - `na` -> N/A (excluded from scoring)
  - no entry -> Missed, **except today**, which stays "pending" (not counted either way) until the day ends.
    (The sheet counted unlogged days as missed; the app keeps today pending so the dashboard does not look worse before you have logged.)

## Formulas
- **Done** = count of Done. **N/A** = count of N/A. **Missed** = applicable - Done.
- **Applicable** = active (goal, day) pairs up to `T` minus N/A (minus pending today).
- **Completion %** = Done / Applicable (0 when Applicable = 0).
- **Daily score** (a day) = Done that day / applicable that day. Applicable = active goals that day minus N/A that day.
- **Perfect day** = a day with applicable > 0 and Done = applicable.
- **Per goal**: same formulas restricted to that goal's active days.
- **Weekly**: weeks start on the challenge's start date (week 1 = days 1-7). `possible` = applicable goal-days in that week; `completion = done / possible`.
- **Monthly** (calendar months clipped to the challenge dates and to `T`): days, done, missed, N/A, completion %, perfect days,
  **average daily score** = mean of daily scores over logged-or-elapsed days in the month, **best day** = max daily score.
- **Per-goal-per-month**: Done, Missed, N/A, Completion for each goal and month, with a TOTAL row.
- **Overall completion / goals completed / perfect days**: the same formulas over the whole challenge to `T`.

## Worked example (from the sheet, 27 Oct 2026, challenge 6 Oct onwards, 10 goals)
- Office before 10 AM: 22 elapsed days, 8 N/A (days off), so applicable = 14. Done = 5, Missed = 14 - 5 = **9**, Completion = 5/14 = **36%**.
- October (22 days x 10 goals = 220 goal-days) with 8 N/A: applicable = 212. Done = 110, Missed = **102**, Completion = 110/212 = **52%**.
- Best single day: 9 of 10 done = **90%**. Average daily score across the 22 days: **51%**.
These figures are test fixtures: the scoring unit tests must reproduce them (Sprint 2). The sheet counted 27 Oct as a full day, so the fixture
sets the as-of date to 28 Oct (27 Oct is then a finished day); evaluated *on* 27 Oct the app shows 21 elapsed days because today is still pending.

## Edge cases
| Case | Rule |
|---|---|
| Goal retired part-way | Counts only through `active_to`; earlier history unchanged |
| Goal added part-way | Counts from `active_from` (defaults to the day it was added, not the challenge start) |
| All goals N/A on a day | Applicable = 0: the day has no score and is neither perfect nor missed |
| Challenge not started | All counts 0, completion shown as "-" |
| Challenge ended | `T` = end date; numbers freeze |
| Timezone change | Entries keep their date; only "today" changes |
| Edit of a past entry | Dashboard and awards recomputed; badges already earned are **not** revoked |

## Streaks
- **Day streak** = consecutive days (ending `T`, or yesterday if today is still pending) that are *successful*.
- A day is **successful** if its daily score >= **80%** (configurable per badge later) and it has applicable goals. A day with no applicable goals neither extends nor breaks the streak.
- **Perfect streak** = consecutive perfect days.
- Longest streak is stored per challenge for the awards page.

## Stars and awards
Each badge is worth stars; total stars = sum over earned badges (counted once per challenge where `challenge_id` is set).
Badge rules live in `badges.rule` (jsonb) so an admin can tune them in Sprint 4.

| Code | Name | Rule | Stars |
|---|---|---|---|
| FIRST_LOG | First check-in | Log any entry | 1 |
| FIRST_PERFECT_DAY | Perfect day | First perfect day | 2 |
| STREAK_3 | Warm-up | 3-day streak | 1 |
| STREAK_7 | One week strong | 7-day streak | 3 |
| STREAK_14 | Two weeks strong | 14-day streak | 5 |
| STREAK_30 | Month of habit | 30-day streak | 10 |
| WEEK_80 | Solid week | A week with completion >= 80% | 2 |
| MONTH_80 | Solid month | A calendar month with completion >= 80% | 5 |
| GOAL_MASTER | Goal master | One goal with >= 90% completion over >= 14 applicable days | 3 |
| COMEBACK | Comeback | Score >= 80% on a day after 3+ days below 50% | 2 |
| HALFWAY | Halfway there | Reach 50% of the challenge's days | 2 |
| CHALLENGE_COMPLETE | Challenge complete | Challenge end date reached with overall completion >= 60% | 10 |
| CHALLENGE_CHAMPION | Champion | Challenge end date reached with overall completion >= 90% | 20 |
Evaluation: after each entry write the backend re-evaluates only the rules the change can affect; a nightly job handles time-based badges
(HALFWAY, CHALLENGE_COMPLETE/CHAMPION). Earning is idempotent (unique constraint) and never revoked.

## What a share shows
Challenge name, owner display name, dates, completion %, current and longest streak, stars and badges earned. The `dashboard` scope also shows
the weekly/monthly tables. Never notes or emails.

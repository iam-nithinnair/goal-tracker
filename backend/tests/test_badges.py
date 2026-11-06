"""One test per badge, just below and just at its threshold (docs/05-scoring-and-awards.md)."""

from datetime import date, timedelta

from app.services.badges import earned_codes
from app.services.scoring import compute_dashboard

START = date(2026, 10, 1)
END = date(2026, 12, 31)
ALWAYS = date(2027, 6, 1)  # well after everything, so no day is "today"


def build(scores_by_day, *, goals=10, today=ALWAYS, end=END, start=START):
    """`scores_by_day[i]` = how many of `goals` goals are done on day i (None = nothing logged)."""
    gl = [
        {"id": f"g{i}", "name": f"G{i}", "active_from": start, "active_to": None}
        for i in range(goals)
    ]
    entries = []
    for i, done in enumerate(scores_by_day):
        if done is None:
            continue
        for g in range(goals):
            entries.append(
                {
                    "goal_id": f"g{g}",
                    "entry_date": start + timedelta(days=i),
                    "status": "yes" if g < done else "no",
                }
            )
    dash = compute_dashboard(start=start, end=end, goals=gl, entries=entries, today=today)
    return dash, len(entries)


def codes(scores_by_day, *, today=ALWAYS, end=END, start=START, goals=10):
    dash, n = build(scores_by_day, today=today, end=end, start=start, goals=goals)
    return set(earned_codes(dash, entry_count=n, start=start, end=end, today=today))


def at_end(days, **kw):  # a challenge ending after `days` so "ended" rules don't interfere
    return {"end": START + timedelta(days=days + 100), **kw}


def test_first_log_needs_an_entry():
    assert "FIRST_LOG" not in codes([], today=date(2026, 10, 5))
    assert "FIRST_LOG" in codes([1], today=date(2026, 10, 5))


def test_first_perfect_day_needs_every_goal():
    assert "FIRST_PERFECT_DAY" not in codes([9, 9], today=date(2026, 10, 5))
    assert "FIRST_PERFECT_DAY" in codes([9, 10], today=date(2026, 10, 5))


def test_a_partly_logged_today_does_not_earn_a_perfect_day():
    today = date(2026, 10, 3)
    gl = {"id": "g0", "name": "G0", "active_from": START, "active_to": None}
    one = compute_dashboard(
        start=START,
        end=END,
        goals=[gl, {**gl, "id": "g1"}],
        entries=[{"goal_id": "g0", "entry_date": today, "status": "yes"}],
        today=today,
    )
    assert "FIRST_PERFECT_DAY" not in earned_codes(
        one, entry_count=1, start=START, end=END, today=today
    )


def streak_scores(n, good=8, bad=7):
    return [good] * n + [bad]


def test_streak_badges_unlock_exactly_at_their_length():
    for code, need in (("STREAK_3", 3), ("STREAK_7", 7), ("STREAK_14", 14), ("STREAK_30", 30)):
        assert code not in codes(streak_scores(need - 1), **at_end(60)), code
        assert code in codes(streak_scores(need), **at_end(60)), code


def test_week_80_needs_a_finished_week_at_80_percent():
    week = lambda done: [done] * 7  # noqa: E731
    assert "WEEK_80" not in codes(
        week(7), today=date(2026, 10, 7)
    )  # week 1 ends on the 7th: not over yet
    assert "WEEK_80" in codes(week(8), today=date(2026, 10, 8))
    assert "WEEK_80" not in codes(week(7), today=date(2026, 10, 8))


def test_month_80_needs_a_finished_month_at_80_percent():
    october = lambda done: [done] * 31  # noqa: E731
    assert "MONTH_80" not in codes(october(8), today=date(2026, 10, 31))  # not over yet
    assert "MONTH_80" in codes(october(8), today=date(2026, 11, 1))
    assert "MONTH_80" not in codes(october(7), today=date(2026, 11, 1))


def test_goal_master_needs_14_applicable_days_at_90_percent():
    # one goal: 13 days is too few; 14 days all done earns it; 12 of 14 (86%) does not
    assert "GOAL_MASTER" not in codes([1] * 13, goals=1, today=date(2026, 10, 14))
    assert "GOAL_MASTER" in codes([1] * 14, goals=1, today=date(2026, 10, 15))
    assert "GOAL_MASTER" not in codes([1] * 12 + [0, 0], goals=1, today=date(2026, 10, 15))


def test_comeback_needs_3_low_days_then_a_good_one():
    assert "COMEBACK" not in codes([4, 4, 9], today=date(2026, 10, 4))  # only 2 low days
    assert "COMEBACK" in codes([4, 4, 4, 8], today=date(2026, 10, 5))
    assert "COMEBACK" not in codes([4, 4, 4, 7], today=date(2026, 10, 5))  # 70% is not a good day
    assert "COMEBACK" not in codes([4, 4, 6, 4, 9], today=date(2026, 10, 6))  # the run was broken


def test_halfway_at_the_midpoint():
    end = date(2026, 10, 20)  # 20 days: halfway once 10 days have elapsed
    assert "HALFWAY" not in codes([5] * 9, today=date(2026, 10, 9), end=end)
    assert "HALFWAY" in codes([5] * 10, today=date(2026, 10, 10), end=end)


def test_challenge_complete_and_champion_need_the_end_and_the_completion():
    end = date(2026, 10, 10)
    year = lambda done: [done] * 10  # noqa: E731
    on_last_day = date(2026, 10, 10)
    assert not codes(year(10), today=on_last_day, end=end) & {
        "CHALLENGE_COMPLETE",
        "CHALLENGE_CHAMPION",
    }
    after = date(2026, 10, 11)
    assert codes(year(6), today=after, end=end) >= {"CHALLENGE_COMPLETE"}
    assert "CHALLENGE_CHAMPION" not in codes(year(8), today=after, end=end)
    assert "CHALLENGE_COMPLETE" not in codes(year(5), today=after, end=end)
    assert codes(year(9), today=after, end=end) >= {"CHALLENGE_COMPLETE", "CHALLENGE_CHAMPION"}


def test_thresholds_come_from_the_catalogue_rules():
    dash, n = build([8, 8], today=ALWAYS, end=date(2026, 12, 31))
    base = dict(entry_count=n, start=START, end=END, today=ALWAYS)
    assert "STREAK_3" not in earned_codes(dash, **base)
    assert "STREAK_3" in earned_codes(dash, **base, rules={"STREAK_3": {"days": 2}})


def test_editing_history_later_does_not_matter_to_a_pure_evaluation():
    """Rows are never deleted (so never revoked); a worse history just yields fewer codes."""
    good = codes([10, 10, 10], today=date(2026, 10, 5))
    worse = codes([0, 0, 0], today=date(2026, 10, 5))
    assert "FIRST_PERFECT_DAY" in good and "FIRST_PERFECT_DAY" not in worse

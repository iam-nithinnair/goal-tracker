"""Streak rules from docs/05-scoring-and-awards.md."""

from datetime import date, timedelta

from app.services.streaks import compute_streaks

START = date(2026, 10, 1)


def day(offset, score, applicable=10):
    done = None if score is None else round(score * applicable)
    return {
        "date": START + timedelta(days=offset),
        "applicable": applicable,
        "score": score,
        "done": done if done is not None else 0,
    }


def run(scores, today_offset=99, **kw):
    days = [day(i, s, **kw) for i, s in enumerate(scores)]
    return compute_streaks(days, START + timedelta(days=today_offset))


def test_consecutive_good_days_build_a_streak():
    assert run([0.9, 0.8, 1.0])["current"] == 3


def test_a_bad_day_breaks_the_streak_and_the_longest_is_kept():
    s = run([0.9, 0.9, 0.9, 0.5, 0.9])
    assert (s["current"], s["longest"]) == (1, 3)


def test_79_percent_is_not_a_successful_day_and_80_is():
    assert run([0.7, 0.8])["current"] == 1
    assert run([0.8])["current"] == 1


def test_a_day_with_nothing_applicable_neither_extends_nor_breaks():
    days = [day(0, 0.9), day(1, None, applicable=0), day(2, 0.9)]
    days[1]["done"] = 0
    s = compute_streaks(days, START + timedelta(days=99))
    assert s["current"] == 2


def test_a_not_yet_good_today_does_not_break_the_streak():
    s = run([0.9, 0.9, 0.1], today_offset=2)  # day 3 is today and only 10% so far
    assert s["current"] == 2


def test_a_good_today_extends_it():
    assert run([0.9, 0.9, 0.9], today_offset=2)["current"] == 3


def test_perfect_streak_needs_every_applicable_goal():
    s = run([1.0, 1.0, 0.9, 1.0])
    assert (s["perfect_current"], s["perfect_longest"]) == (1, 2)


def test_no_days_means_no_streaks():
    assert compute_streaks([], START) == {
        "current": 0,
        "longest": 0,
        "perfect_current": 0,
        "perfect_longest": 0,
    }

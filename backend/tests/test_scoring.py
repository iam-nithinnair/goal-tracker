"""Scoring rules from docs/05-scoring-and-awards.md. Pure functions, no database."""

import random
from datetime import date, timedelta

import pytest

from app.services.scoring import compute_dashboard, ratio
from tests import golden_winter_arc as golden

D = date


def goal(gid="a", name="A", active_from=None, active_to=None):
    active_from = active_from or D(2026, 10, 1)
    return {"id": gid, "name": name, "active_from": active_from, "active_to": active_to}


def entry(gid, day, status):
    return {"goal_id": gid, "entry_date": day, "status": status}


def dash(goals, entries, today, start=None, end=None):
    start, end = start or D(2026, 10, 1), end or D(2026, 10, 10)
    return compute_dashboard(start=start, end=end, goals=goals, entries=entries, today=today)


# ---------------------------------------------------------------- golden fixture
@pytest.fixture(scope="module")
def sheet():
    return compute_dashboard(
        start=golden.START,
        end=golden.END,
        goals=golden.goals(),
        entries=golden.entries(),
        today=golden.AS_OF_TODAY,
    )


def test_golden_office_before_10_matches_the_sheet(sheet):
    office = next(g for g in sheet["goals"] if g["name"] == "Office before 10 AM")
    assert (office["done"], office["missed"], office["na"]) == (5, 9, 8)
    assert round(office["completion"], 2) == 0.36


def test_golden_october_matches_the_sheet(sheet):
    october = next(m for m in sheet["months"] if m["month"] == "2026-10")
    assert (october["days"], october["done"], october["missed"], october["na"]) == (22, 113, 99, 8)
    assert round(october["completion"], 2) == 0.53
    assert round(october["best_day"], 2) == 0.90
    assert round(october["avg_daily_score"], 2) == 0.53


def test_golden_matches_a_plain_tally_of_the_marks(sheet):
    """Independent of the engine: count the Y/N/A characters directly."""
    flat = "".join(golden.MARKS)
    k = sheet["kpis"]
    assert (k["goals_completed"], k["missed"], k["na"]) == (
        flat.count("Y"),
        flat.count("N"),
        flat.count("A"),
    )


def test_golden_kpis_and_totals_agree(sheet):
    k = sheet["kpis"]
    assert (k["days_in"], k["days_left"], k["total_days"]) == (22, 65, 87)
    assert k["goals_completed"] == 113
    assert k["perfect_days"] == 0
    # the October row is the whole challenge so far, so it equals the overall KPIs
    assert sum(m["done"] for m in sheet["months"]) == k["goals_completed"]
    assert sum(g["done"] for g in sheet["goals"]) == k["goals_completed"]
    assert sum(w["done"] for w in sheet["weeks"]) == k["goals_completed"]
    assert sum(r["done"] for r in sheet["days"]) == k["goals_completed"]


def test_golden_future_months_and_weeks_are_empty(sheet):
    december = next(m for m in sheet["months"] if m["month"] == "2026-12")
    assert december["days"] == 0 and december["completion"] is None
    assert sheet["weeks"][-1]["possible"] == 0 and sheet["weeks"][-1]["completion"] is None
    assert sheet["weeks"][0]["from"] == golden.START
    assert sheet["weeks"][-1]["to"] == golden.END  # last week is clipped to the challenge


# ---------------------------------------------------------------- rules and edge cases
def test_unlogged_past_days_are_missed():
    out = dash([goal()], [entry("a", D(2026, 10, 1), "yes")], today=D(2026, 10, 4))
    g = out["goals"][0]
    assert (g["done"], g["missed"], g["na"]) == (1, 2, 0)  # 2 Oct and 3 Oct unlogged
    assert out["kpis"]["days_in"] == 3


def test_today_stays_pending_until_logged():
    out = dash([goal()], [], today=D(2026, 10, 3))
    assert out["goals"][0]["missed"] == 2  # 1 and 2 Oct; today (3 Oct) not counted
    assert out["kpis"]["days_in"] == 2
    assert out["days"][-1]["date"] == D(2026, 10, 2)


def test_a_logged_today_counts():
    out = dash([goal()], [entry("a", D(2026, 10, 3), "yes")], today=D(2026, 10, 3))
    assert out["goals"][0]["done"] == 1
    assert out["kpis"]["days_in"] == 3


def test_na_is_excluded_from_the_denominator():
    entries = [entry("a", D(2026, 10, 1), "yes"), entry("a", D(2026, 10, 2), "na")]
    out = dash([goal()], entries, today=D(2026, 10, 3))
    g = out["goals"][0]
    assert (g["done"], g["missed"], g["na"]) == (1, 0, 1)
    assert g["completion"] == 1.0


def test_all_na_day_has_no_score_and_is_not_perfect():
    out = dash([goal()], [entry("a", D(2026, 10, 1), "na")], today=D(2026, 10, 2))
    day = out["days"][0]
    assert day["applicable"] == 0 and day["score"] is None
    assert out["kpis"]["perfect_days"] == 0
    assert out["kpis"]["overall_completion"] is None


def test_perfect_day_needs_every_applicable_goal_done():
    goals = [goal("a"), goal("b", "B")]
    entries = [
        entry("a", D(2026, 10, 1), "yes"),
        entry("b", D(2026, 10, 1), "yes"),
        entry("a", D(2026, 10, 2), "yes"),
        entry("b", D(2026, 10, 2), "no"),
        entry("a", D(2026, 10, 3), "yes"),
        entry("b", D(2026, 10, 3), "na"),
    ]
    out = dash(goals, entries, today=D(2026, 10, 4))
    assert out["kpis"]["perfect_days"] == 2  # day 1, and day 3 where b is N/A


def test_retired_goal_stops_counting_but_keeps_history():
    g = goal(active_to=D(2026, 10, 2))
    out = dash([g], [entry("a", D(2026, 10, 1), "yes")], today=D(2026, 10, 6))
    row = out["goals"][0]
    assert (row["done"], row["missed"]) == (1, 1)  # 1 and 2 Oct only
    assert row["retired"] is True


def test_goal_added_part_way_counts_from_its_start():
    g = goal(active_from=D(2026, 10, 3))
    out = dash([g], [], today=D(2026, 10, 5))
    assert out["goals"][0]["missed"] == 2  # 3 and 4 Oct


def test_challenge_not_started_is_all_zero():
    out = dash([goal()], [], today=D(2026, 9, 20))
    assert out["kpis"]["days_in"] == 0
    assert out["kpis"]["overall_completion"] is None
    assert out["goals"][0]["completion"] is None
    assert out["days"] == []


def test_finished_challenge_freezes_at_the_end_date():
    out = dash([goal()], [entry("a", D(2026, 10, 1), "yes")], today=D(2027, 3, 1))
    assert out["as_of"] == D(2026, 10, 10)
    assert out["kpis"]["days_in"] == 10 and out["kpis"]["days_left"] == 0
    assert out["goals"][0]["missed"] == 9


def test_weeks_start_on_the_challenge_start_and_the_last_is_partial():
    out = dash([goal()], [], today=D(2026, 10, 12), start=D(2026, 10, 1), end=D(2026, 10, 10))
    assert [(w["from"], w["to"]) for w in out["weeks"]] == [
        (D(2026, 10, 1), D(2026, 10, 7)),
        (D(2026, 10, 8), D(2026, 10, 10)),
    ]
    assert out["weeks"][1]["possible"] == 3


def test_months_are_clipped_to_the_challenge():
    out = dash([goal()], [], today=D(2026, 11, 20), start=D(2026, 10, 28), end=D(2026, 11, 3))
    october, november = out["months"]
    assert (october["month"], october["days"]) == ("2026-10", 4)  # 28-31 Oct
    assert (november["month"], november["days"]) == ("2026-11", 3)


def test_ratio_handles_zero():
    assert ratio(0, 0) is None
    assert ratio(1, 4) == 0.25


def test_every_active_goal_day_is_done_missed_na_or_pending():
    """Property: Done + Missed + N/A + pending equals the active goal-days up to the as-of date."""
    rng = random.Random(7)
    for _ in range(40):
        start = D(2026, 10, 1)
        end = start + timedelta(days=rng.randint(5, 40))
        today = start + timedelta(days=rng.randint(-3, 50))
        goals = []
        for i in range(rng.randint(1, 5)):
            a = start + timedelta(days=rng.randint(0, 5))
            b = a + timedelta(days=rng.randint(0, 30)) if rng.random() < 0.4 else None
            goals.append(goal(f"g{i}", f"G{i}", a, b))
        entries = [
            entry(g["id"], start + timedelta(days=d), rng.choice(["yes", "no", "na"]))
            for g in goals
            for d in range(0, (min(today, end) - start).days + 1)
            if rng.random() < 0.6
            and g["active_from"] <= start + timedelta(days=d)
            and (g["active_to"] is None or start + timedelta(days=d) <= g["active_to"])
        ]
        out = dash(goals, entries, today, start=start, end=end)

        as_of = min(today, end)
        active = pending = 0
        logged = {(e["goal_id"], e["entry_date"]) for e in entries}
        d = start
        while d <= as_of:
            for g in goals:
                if g["active_from"] <= d and (g["active_to"] is None or d <= g["active_to"]):
                    active += 1
                    pending += d == today and (g["id"], d) not in logged
            d += timedelta(days=1)
        k = out["kpis"]
        assert k["goals_completed"] + k["missed"] + k["na"] + pending == active
        assert sum(m["done"] + m["missed"] + m["na"] for m in out["months"]) == active - pending

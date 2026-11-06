"""Badges, stars and the awards endpoints against the local Supabase stack."""

from datetime import timedelta

import pytest

from tests.test_api_integration import API, _rest, iso, make_challenge, today

pytestmark = pytest.mark.integration


def log_day(client, user, challenge, day, status="yes"):
    r = client.put(
        f"{API}/challenges/{challenge['id']}/entries/{iso(day)}",
        headers=user.headers,
        json={"entries": [{"goal_id": g["id"], "status": status} for g in challenge["goals"]]},
    )
    assert r.status_code == 200, r.text
    return [b["code"] for b in r.json()["new_badges"]]


def test_first_entry_unlocks_first_log_once(client, alice):
    c = make_challenge(client, alice)
    goal = c["goals"][0]["id"]
    put = lambda: client.put(  # noqa: E731
        f"{API}/goals/{goal}/entries/{iso(today())}",
        headers=alice.headers,
        json={"status": "yes"},
    )
    first = put().json()["new_badges"]
    assert [b["code"] for b in first] == ["FIRST_LOG"]
    assert first[0]["stars"] == 1 and first[0]["name"]
    assert put().json()["new_badges"] == []  # writing the same entry again earns nothing twice


def test_a_perfect_day_unlocks_the_badge_and_the_stars_add_up(client, alice):
    c = make_challenge(client, alice)
    new = log_day(client, alice, c, today() - timedelta(days=1))
    assert set(new) >= {"FIRST_LOG", "FIRST_PERFECT_DAY"}

    badges = client.get(f"{API}/badges", headers=alice.headers).json()
    assert len(badges) == 13
    by = {b["code"]: b for b in badges}
    assert by["FIRST_PERFECT_DAY"]["earned_on"] is not None
    assert by["FIRST_PERFECT_DAY"]["earned"][0]["challenge_id"] == c["id"]
    assert by["STREAK_30"]["earned_on"] is None and by["STREAK_30"]["earned"] == []

    stars = client.get(f"{API}/me/stars", headers=alice.headers).json()
    expected = sum(b["stars"] for b in badges if b["earned_on"])
    assert stars["total_stars"] == expected > 0
    assert stars["by_challenge"][0]["challenge_id"] == c["id"]


def test_the_same_badge_in_two_challenges_counts_in_each(client, alice):
    one, two = make_challenge(client, alice, name="One"), make_challenge(client, alice, name="Two")
    for c in (one, two):
        log_day(client, alice, c, today() - timedelta(days=1))
    stars = client.get(f"{API}/me/stars", headers=alice.headers).json()
    assert len(stars["by_challenge"]) == 2
    assert stars["total_stars"] == sum(c["stars"] for c in stars["by_challenge"])
    only_one = client.get(
        f"{API}/badges", headers=alice.headers, params={"challenge_id": one["id"]}
    )
    assert {e["challenge_id"] for b in only_one.json() for e in b["earned"]} == {one["id"]}


def test_editing_history_later_does_not_revoke_a_badge(client, alice):
    c = make_challenge(client, alice)
    yesterday = today() - timedelta(days=1)
    assert "FIRST_PERFECT_DAY" in log_day(client, alice, c, yesterday)
    log_day(client, alice, c, yesterday, status="no")  # rewrite the day as a total miss
    by = {b["code"]: b for b in client.get(f"{API}/badges", headers=alice.headers).json()}
    assert by["FIRST_PERFECT_DAY"]["earned_on"] is not None


def test_halfway_is_awarded_when_viewing_awards_without_any_new_check_in(client, alice):
    c = make_challenge(
        client, alice, start=today() - timedelta(days=10), end=today() + timedelta(days=9)
    )
    client.put(
        f"{API}/goals/{c['goals'][0]['id']}/entries/{iso(today() - timedelta(days=10))}",
        headers=alice.headers,
        json={"status": "yes"},
    )
    by = {b["code"]: b for b in client.get(f"{API}/badges", headers=alice.headers).json()}
    assert by["HALFWAY"]["earned_on"] is not None  # 20-day challenge, 11 days in


def test_clients_cannot_award_themselves_or_read_other_peoples_badges(client, alice, bob):
    c = make_challenge(client, alice)
    log_day(client, alice, c, today() - timedelta(days=1))
    assert (
        len(_rest("user_badges", alice.token).json()) >= 2
    )  # alice can read her own rows directly

    assert _rest("user_badges", bob.token).json() == []  # bob can't see them
    forged = _rest(
        "user_badges",
        bob.token,
        "POST",
        {
            "user_id": bob.id,
            "badge_code": "CHALLENGE_CHAMPION",
            "challenge_id": c["id"],
            "earned_on": iso(today()),
        },
    )
    assert forged.status_code in (401, 403)  # and can't insert one, even for himself
    forged_own = _rest(
        "user_badges",
        alice.token,
        "POST",
        {
            "user_id": alice.id,
            "badge_code": "CHALLENGE_CHAMPION",
            "challenge_id": c["id"],
            "earned_on": iso(today()),
        },
    )
    assert forged_own.status_code in (401, 403)
    assert _rest("user_badges", None).status_code in (401, 403) or _rest("user_badges").json() == []


def test_the_job_endpoint_is_invisible_without_the_secret(client, alice):
    assert client.post(f"{API}/internal/jobs/awards").status_code == 404
    assert (
        client.post(f"{API}/internal/jobs/awards", headers={"X-Job-Secret": "wrong"}).status_code
        == 404
    )
    assert client.get(f"{API}/badges").status_code == 401

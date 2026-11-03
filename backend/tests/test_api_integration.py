"""End-to-end API tests against the local Supabase stack, including cross-user isolation."""

from datetime import UTC, datetime, timedelta

import httpx
import pytest

from app.core.config import get_settings

pytestmark = pytest.mark.integration

API = "/api/v1"
TEMPLATE_ID = "00000000-0000-4000-8000-000000000001"


def today():
    return datetime.now(UTC).date()


def iso(d):
    return d.isoformat()


def make_challenge(
    client, user, *, goals=("Run", "Read", "Sleep"), start=None, end=None, name="Test"
):
    start = start or today() - timedelta(days=10)
    end = end or today() + timedelta(days=20)
    r = client.post(
        f"{API}/challenges",
        headers=user.headers,
        json={"name": name, "start_date": iso(start), "end_date": iso(end), "goals": list(goals)},
    )
    assert r.status_code == 201, r.text
    return r.json()


# ---------------------------------------------------------------- profile
def test_profile_is_created_on_signup_and_readable(client, alice):
    r = client.get(f"{API}/me", headers=alice.headers)
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == alice.id
    assert body["email"] == alice.email
    assert body["role"] == "user"
    assert body["timezone"] == "UTC"
    assert body["display_name"] == alice.email.split("@")[0]


def test_profile_update_validates_and_never_accepts_role(client, alice):
    ok = client.patch(
        f"{API}/me",
        headers=alice.headers,
        json={"display_name": "  Ali  ", "timezone": "Asia/Kolkata", "avatar_color": "#112233"},
    )
    assert ok.status_code == 200
    assert ok.json()["display_name"] == "Ali"
    assert ok.json()["timezone"] == "Asia/Kolkata"

    bad = client.patch(f"{API}/me", headers=alice.headers, json={"timezone": "Mars/Olympus"})
    assert bad.status_code == 400
    assert bad.json()["error"]["code"] == "validation_error"
    assert "timezone" in bad.json()["error"]["fields"]

    # an unknown `role` field is ignored, never applied
    client.patch(f"{API}/me", headers=alice.headers, json={"role": "super_admin"})
    assert client.get(f"{API}/me", headers=alice.headers).json()["role"] == "user"


# ---------------------------------------------------------------- challenges
def test_templates_list_has_winter_arc_with_ten_goals(client, alice):
    r = client.get(f"{API}/templates", headers=alice.headers)
    assert r.status_code == 200
    winter = next(t for t in r.json() if t["id"] == TEMPLATE_ID)
    assert winter["name"] == "Winter Arc 2026"
    assert [g["name"] for g in winter["goals"]][:3] == [
        "Wake up 8 AM",
        "Cold shower",
        "Office before 10 AM",
    ]
    assert len(winter["goals"]) == 10


def test_create_from_template_copies_goals_without_touching_the_template(client, alice):
    created = client.post(
        f"{API}/challenges",
        headers=alice.headers,
        json={
            "name": "My Arc",
            "start_date": iso(today()),
            "end_date": iso(today() + timedelta(days=29)),
            "template_id": TEMPLATE_ID,
        },
    ).json()
    assert len(created["goals"]) == 10
    assert all(g["active_from"] == iso(today()) for g in created["goals"])
    assert [g["position"] for g in created["goals"]] == list(range(1, 11))

    # editing the copy leaves the template alone
    client.patch(
        f"{API}/goals/{created['goals'][0]['id']}", headers=alice.headers, json={"name": "Changed"}
    )
    tmpl = next(
        t
        for t in client.get(f"{API}/templates", headers=alice.headers).json()
        if t["id"] == TEMPLATE_ID
    )
    assert tmpl["goals"][0]["name"] == "Wake up 8 AM"


@pytest.mark.parametrize(
    "patch",
    [
        {"name": ""},
        {"name": "x" * 81},
        {"end_date": "2000-01-01"},  # before start
    ],
)
def test_create_challenge_validation(client, alice, patch):
    body = {
        "name": "ok",
        "start_date": iso(today()),
        "end_date": iso(today() + timedelta(days=5)),
        **patch,
    }
    r = client.post(f"{API}/challenges", headers=alice.headers, json=body)
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "validation_error"


def test_challenge_longer_than_366_days_is_rejected(client, alice):
    body = {"name": "long", "start_date": "2028-01-01", "end_date": "2029-01-01"}
    assert client.post(f"{API}/challenges", headers=alice.headers, json=body).status_code == 400


def test_list_get_archive_and_delete(client, alice):
    c = make_challenge(client, alice)
    assert any(
        x["id"] == c["id"] for x in client.get(f"{API}/challenges", headers=alice.headers).json()
    )
    assert client.get(f"{API}/challenges/{c['id']}", headers=alice.headers).json()["name"] == "Test"

    arch = client.patch(
        f"{API}/challenges/{c['id']}", headers=alice.headers, json={"status": "archived"}
    )
    assert arch.json()["status"] == "archived"
    active = client.get(f"{API}/challenges?status=active", headers=alice.headers).json()
    assert all(x["id"] != c["id"] for x in active)

    # delete needs explicit confirmation
    assert client.delete(f"{API}/challenges/{c['id']}", headers=alice.headers).status_code == 400
    assert (
        client.delete(f"{API}/challenges/{c['id']}?confirm=true", headers=alice.headers).status_code
        == 204
    )
    assert client.get(f"{API}/challenges/{c['id']}", headers=alice.headers).status_code == 404


def test_dates_cannot_exclude_logged_days(client, alice):
    c = make_challenge(client, alice, start=today() - timedelta(days=10))
    goal = c["goals"][0]["id"]
    logged_day = today() - timedelta(days=5)
    assert (
        client.put(
            f"{API}/goals/{goal}/entries/{iso(logged_day)}",
            headers=alice.headers,
            json={"status": "yes"},
        ).status_code
        == 200
    )

    late_start = client.patch(
        f"{API}/challenges/{c['id']}",
        headers=alice.headers,
        json={"start_date": iso(today() - timedelta(days=2))},
    )
    assert late_start.status_code == 409
    assert late_start.json()["error"]["code"] == "dates_exclude_entries"

    early_end = client.patch(
        f"{API}/challenges/{c['id']}",
        headers=alice.headers,
        json={"end_date": iso(today() - timedelta(days=7))},
    )
    assert early_end.status_code == 409

    # widening is fine, and goal windows follow the new start
    widened = client.patch(
        f"{API}/challenges/{c['id']}",
        headers=alice.headers,
        json={"start_date": iso(today() - timedelta(days=15))},
    ).json()
    assert all(g["active_from"] == iso(today() - timedelta(days=15)) for g in widened["goals"])


# ---------------------------------------------------------------- goals
def test_add_rename_reorder_retire_delete(client, alice):
    c = make_challenge(client, alice, goals=("A", "B", "C"))
    cid = c["id"]
    a, b, cc = (g["id"] for g in c["goals"])

    new = client.post(
        f"{API}/challenges/{cid}/goals", headers=alice.headers, json={"name": "  D  "}
    )
    assert new.status_code == 201 and new.json()["name"] == "D" and new.json()["position"] == 4

    assert (
        client.patch(f"{API}/goals/{a}", headers=alice.headers, json={"name": "A2"}).json()["name"]
        == "A2"
    )
    assert (
        client.patch(f"{API}/goals/{a}", headers=alice.headers, json={"name": ""}).status_code
        == 400
    )

    d = new.json()["id"]
    order = client.put(
        f"{API}/challenges/{cid}/goals/order",
        headers=alice.headers,
        json={"goal_ids": [d, cc, b, a]},
    )
    assert [g["id"] for g in order.json()] == [d, cc, b, a]
    # must list every goal exactly once
    assert (
        client.put(
            f"{API}/challenges/{cid}/goals/order", headers=alice.headers, json={"goal_ids": [d, cc]}
        ).status_code
        == 400
    )

    last_day = iso(today() - timedelta(days=3))
    retired = client.post(f"{API}/goals/{b}/retire", headers=alice.headers, json={"on": last_day})
    assert retired.status_code == 200 and retired.json()["active_to"] == last_day
    too_late = client.post(
        f"{API}/goals/{b}/retire",
        headers=alice.headers,
        json={"on": iso(today() + timedelta(days=400))},
    )
    assert too_late.status_code == 400

    assert (
        client.delete(f"{API}/goals/{cc}", headers=alice.headers).status_code == 400
    )  # needs confirm
    assert client.delete(f"{API}/goals/{cc}?confirm=true", headers=alice.headers).status_code == 204
    left = client.get(f"{API}/challenges/{cid}", headers=alice.headers).json()["goals"]
    assert cc not in [g["id"] for g in left]


# ---------------------------------------------------------------- entries
def test_entry_upsert_is_idempotent_last_write_wins_and_clearable(client, alice):
    c = make_challenge(client, alice)
    goal, day = c["goals"][0]["id"], iso(today())
    url = f"{API}/goals/{goal}/entries/{day}"

    for status in ("yes", "yes", "no", "na"):
        r = client.put(url, headers=alice.headers, json={"status": status})
        assert r.status_code == 200
        assert r.json()["entries"][0]["status"] == status
        assert r.json()["new_badges"] == []

    rows = client.get(f"{API}/challenges/{c['id']}/entries", headers=alice.headers).json()
    assert [(e["goal_id"], e["entry_date"], e["status"]) for e in rows] == [(goal, day, "na")]

    assert client.put(url, headers=alice.headers, json={"status": "maybe"}).status_code == 400
    assert client.delete(url, headers=alice.headers).status_code == 204
    assert client.get(f"{API}/challenges/{c['id']}/entries", headers=alice.headers).json() == []


def test_entry_date_rules(client, alice):
    c = make_challenge(
        client, alice, start=today() - timedelta(days=10), end=today() + timedelta(days=20)
    )
    goal = c["goals"][0]["id"]

    def put(day):
        return client.put(
            f"{API}/goals/{goal}/entries/{iso(day)}", headers=alice.headers, json={"status": "yes"}
        )

    assert put(today()).status_code == 200  # today
    assert put(today() - timedelta(days=10)).status_code == 200  # first day (backfill)
    assert put(today() + timedelta(days=1)).status_code == 400  # future
    assert put(today() - timedelta(days=11)).status_code == 400  # before the challenge

    # a retired goal can't be logged after its last day
    client.post(
        f"{API}/goals/{goal}/retire",
        headers=alice.headers,
        json={"on": iso(today() - timedelta(days=4))},
    )
    assert put(today() - timedelta(days=4)).status_code == 200
    after = put(today() - timedelta(days=3))
    assert after.status_code == 400 and "active" in after.json()["error"]["message"]


def test_today_uses_the_users_timezone(client, alice):
    """At any moment the date differs between UTC+14 and UTC-12 by about a day, so a user in
    Kiritimati can log 'tomorrow' (UTC) while a user in Baker Island cannot log 'today' (UTC)."""
    ahead = client.patch(
        f"{API}/me", headers=alice.headers, json={"timezone": "Pacific/Kiritimati"}
    )
    assert ahead.status_code == 200
    c = make_challenge(
        client, alice, start=today() - timedelta(days=3), end=today() + timedelta(days=5)
    )
    goal = c["goals"][0]["id"]
    tomorrow_utc = today() + timedelta(days=1)
    from app.services.dates import today_in

    local_today = today_in("Pacific/Kiritimati")
    r = client.put(
        f"{API}/goals/{goal}/entries/{iso(local_today)}",
        headers=alice.headers,
        json={"status": "yes"},
    )
    assert r.status_code == 200
    # one day beyond *their* today is still the future for them
    beyond = client.put(
        f"{API}/goals/{goal}/entries/{iso(local_today + timedelta(days=1))}",
        headers=alice.headers,
        json={"status": "yes"},
    )
    assert beyond.status_code == 400
    assert local_today >= tomorrow_utc or local_today == today()  # sanity: never behind UTC


def test_log_a_whole_day_at_once(client, alice):
    c = make_challenge(client, alice, goals=("A", "B"))
    day = iso(today() - timedelta(days=1))
    body = {
        "entries": [
            {"goal_id": g["id"], "status": s}
            for g, s in zip(c["goals"], ("yes", "na"), strict=True)
        ]
    }
    r = client.put(f"{API}/challenges/{c['id']}/entries/{day}", headers=alice.headers, json=body)
    assert r.status_code == 200 and len(r.json()["entries"]) == 2
    got = client.get(
        f"{API}/challenges/{c['id']}/entries?from={day}&to={day}", headers=alice.headers
    ).json()
    assert sorted(e["status"] for e in got) == ["na", "yes"]


def test_entry_range_filter(client, alice):
    c = make_challenge(client, alice)
    goal = c["goals"][0]["id"]
    for back in (0, 1, 2, 3):
        client.put(
            f"{API}/goals/{goal}/entries/{iso(today() - timedelta(days=back))}",
            headers=alice.headers,
            json={"status": "yes"},
        )
    got = client.get(
        f"{API}/challenges/{c['id']}/entries"
        f"?from={iso(today() - timedelta(days=2))}&to={iso(today() - timedelta(days=1))}",
        headers=alice.headers,
    ).json()
    assert [e["entry_date"] for e in got] == [
        iso(today() - timedelta(days=2)),
        iso(today() - timedelta(days=1)),
    ]


# ---------------------------------------------------------------- isolation (S1-T13)
def test_other_users_data_is_invisible_through_the_api(client, alice, bob):
    c = make_challenge(client, alice)
    goal = c["goals"][0]["id"]
    day = iso(today())
    client.put(f"{API}/goals/{goal}/entries/{day}", headers=alice.headers, json={"status": "yes"})

    # bob's list is empty of alice's data
    assert all(
        x["id"] != c["id"] for x in client.get(f"{API}/challenges", headers=bob.headers).json()
    )

    probes = [
        ("get", f"{API}/challenges/{c['id']}", None),
        ("patch", f"{API}/challenges/{c['id']}", {"name": "pwned"}),
        ("delete", f"{API}/challenges/{c['id']}?confirm=true", None),
        ("post", f"{API}/challenges/{c['id']}/goals", {"name": "x"}),
        ("put", f"{API}/challenges/{c['id']}/goals/order", {"goal_ids": [goal]}),
        ("get", f"{API}/challenges/{c['id']}/entries", None),
        (
            "put",
            f"{API}/challenges/{c['id']}/entries/{day}",
            {"entries": [{"goal_id": goal, "status": "no"}]},
        ),
        ("patch", f"{API}/goals/{goal}", {"name": "pwned"}),
        ("post", f"{API}/goals/{goal}/retire", {"on": day}),
        ("delete", f"{API}/goals/{goal}?confirm=true", None),
        ("put", f"{API}/goals/{goal}/entries/{day}", {"status": "no"}),
        ("delete", f"{API}/goals/{goal}/entries/{day}", None),
    ]
    for method, url, body in probes:
        r = getattr(client, method)(
            url, headers=bob.headers, **({"json": body} if body is not None else {})
        )
        assert r.status_code == 404, f"{method.upper()} {url} -> {r.status_code}"
        assert r.json()["error"]["code"] == "not_found"

    # and nothing of alice's changed
    same = client.get(f"{API}/challenges/{c['id']}", headers=alice.headers).json()
    assert same["name"] == "Test" and len(same["goals"]) == 3
    assert (
        client.get(f"{API}/challenges/{c['id']}/entries", headers=alice.headers).json()[0]["status"]
        == "yes"
    )


def test_anonymous_and_garbage_tokens_get_401(client):
    assert client.get(f"{API}/challenges").status_code == 401
    assert (
        client.get(f"{API}/challenges", headers={"Authorization": "Bearer nope"}).status_code == 401
    )


# ---------------------------------------------------------------- RLS (direct database access)
def _rest(path, token=None, method="GET", json=None, params=None):
    s = get_settings()
    headers = {"apikey": s.supabase_anon_key}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return httpx.request(
        method,
        f"{s.supabase_url}/rest/v1/{path}",
        headers=headers,
        json=json,
        params=params,
        timeout=20,
    )


def test_rls_blocks_cross_user_and_anonymous_access_directly(client, alice, bob):
    c = make_challenge(client, alice)
    goal = c["goals"][0]["id"]
    client.put(
        f"{API}/goals/{goal}/entries/{iso(today())}", headers=alice.headers, json={"status": "yes"}
    )

    # alice, directly through PostgREST, sees her own rows
    assert [
        r["id"] for r in _rest("challenges", alice.token, params={"id": f"eq.{c['id']}"}).json()
    ] == [c["id"]]
    assert len(_rest("daily_entries", alice.token).json()) == 1

    # bob sees none of them, and can't change or delete them
    assert _rest("challenges", bob.token, params={"id": f"eq.{c['id']}"}).json() == []
    assert _rest("goals", bob.token, params={"id": f"eq.{goal}"}).json() == []
    assert _rest("daily_entries", bob.token).json() == []
    upd = _rest("challenges", bob.token, "PATCH", {"name": "pwned"}, {"id": f"eq.{c['id']}"})
    assert (
        upd.status_code in (200, 204)
        and client.get(f"{API}/challenges/{c['id']}", headers=alice.headers).json()["name"]
        == "Test"
    )
    _rest("daily_entries", bob.token, "DELETE")
    assert len(_rest("daily_entries", alice.token).json()) == 1

    # bob can't write into alice's challenge
    forged = _rest(
        "goals",
        bob.token,
        "POST",
        {"challenge_id": c["id"], "name": "x", "active_from": iso(today())},
    )
    assert forged.status_code in (401, 403)

    # anonymous callers get nothing at all
    for table in ("profiles", "challenges", "goals", "daily_entries"):
        r = _rest(table)
        assert r.status_code in (401, 403) or r.json() == [], (
            f"{table}: {r.status_code} {r.text[:80]}"
        )


def test_rls_user_cannot_promote_themselves_or_edit_templates(alice):
    promote = _rest(
        "profiles", alice.token, "PATCH", {"role": "super_admin"}, {"id": f"eq.{alice.id}"}
    )
    assert promote.status_code >= 400  # privileged columns are protected
    assert (
        _rest("profiles", alice.token, params={"id": f"eq.{alice.id}"}).json()[0]["role"] == "user"
    )

    tmpl = _rest(
        "challenges", alice.token, "PATCH", {"name": "hacked"}, {"id": f"eq.{TEMPLATE_ID}"}
    )
    assert tmpl.status_code in (200, 204)  # RLS filters the row out rather than erroring
    names = _rest("challenges", alice.token, params={"id": f"eq.{TEMPLATE_ID}"}).json()
    assert names[0]["name"] == "Winter Arc 2026"
    assert _rest(
        "challenges", alice.token, "DELETE", params={"id": f"eq.{TEMPLATE_ID}"}
    ).status_code in (200, 204)
    assert (
        len(_rest("goals", alice.token, params={"challenge_id": f"eq.{TEMPLATE_ID}"}).json()) == 10
    )


def test_db_trigger_rejects_entries_outside_the_challenge(alice):
    s = get_settings()
    # use the service role to bypass the API's own checks and hit the DB safety net directly
    headers = {
        "apikey": s.supabase_service_role_key,
        "Authorization": f"Bearer {s.supabase_service_role_key}",
    }
    ch = httpx.post(
        f"{s.supabase_url}/rest/v1/challenges",
        headers={**headers, "Prefer": "return=representation"},
        json={
            "owner_id": alice.id,
            "name": "t",
            "start_date": "2026-01-01",
            "end_date": "2026-01-10",
        },
    ).json()[0]
    g = httpx.post(
        f"{s.supabase_url}/rest/v1/goals",
        headers={**headers, "Prefer": "return=representation"},
        json={"challenge_id": ch["id"], "name": "g", "active_from": "2026-01-01"},
    ).json()[0]
    bad = httpx.post(
        f"{s.supabase_url}/rest/v1/daily_entries",
        headers=headers,
        json={"goal_id": g["id"], "entry_date": "2026-02-01", "status": "yes"},
    )
    assert bad.status_code == 400 and "outside the challenge" in bad.text

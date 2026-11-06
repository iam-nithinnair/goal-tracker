"""Public links, friends and shared challenges against the local Supabase stack."""

import json
from datetime import UTC, datetime, timedelta

import pytest

from app.db.repo import get_client
from app.routers import share_links
from app.services.sharing import RateLimiter
from tests.test_api_integration import API, _rest, iso, make_challenge, today

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------- helpers
def log_today(client, user, challenge):
    for g in challenge["goals"]:
        client.put(
            f"{API}/goals/{g['id']}/entries/{iso(today())}",
            headers=user.headers,
            json={"status": "yes"},
        )


def new_link(client, user, challenge, scope="dashboard", **extra):
    r = client.post(
        f"{API}/challenges/{challenge['id']}/share-links",
        headers=user.headers,
        json={"scope": scope, **extra},
    )
    assert r.status_code == 201, r.text
    return r.json()


def public(client, token):
    return client.get(f"{API}/public/share/{token}")


def befriend(client, a, b):
    assert (
        client.post(
            f"{API}/friends/requests", headers=a.headers, json={"email": b.email}
        ).status_code
        == 202
    )
    incoming = client.get(f"{API}/friends", headers=b.headers).json()["incoming"]
    assert len(incoming) == 1
    r = client.post(f"{API}/friends/requests/{incoming[0]['id']}/accept", headers=b.headers)
    assert r.status_code == 204, r.text


# ---------------------------------------------------------------- public links
def test_link_lifecycle_token_shown_once_then_revoked(client, alice):
    c = make_challenge(client, alice)
    log_today(client, alice, c)
    created = new_link(client, alice, c)
    token = created["token"]
    assert created["path"] == f"/s/{token}" and len(token) >= 43

    listing = client.get(f"{API}/challenges/{c['id']}/share-links", headers=alice.headers).json()
    assert [row["id"] for row in listing] == [created["id"]]
    assert token not in json.dumps(listing) and "token" not in listing[0]

    # only a hash is stored, never the token
    stored = get_client().table("share_links").select("*").eq("id", created["id"]).execute().data[0]
    assert stored["token_hash"] != token and token not in json.dumps(stored)

    assert public(client, token).status_code == 200  # no Authorization header at all
    assert (
        client.delete(f"{API}/share-links/{created['id']}", headers=alice.headers).status_code
        == 204
    )
    assert public(client, token).status_code == 404  # revoked at once


def test_unknown_revoked_and_expired_links_are_indistinguishable(client, alice):
    c = make_challenge(client, alice)
    revoked = new_link(client, alice, c)
    client.delete(f"{API}/share-links/{revoked['id']}", headers=alice.headers)
    expired = new_link(
        client, alice, c, expires_at=(datetime.now(UTC) + timedelta(days=1)).isoformat()
    )
    get_client().table("share_links").update(
        {"expires_at": (datetime.now(UTC) - timedelta(minutes=1)).isoformat()}
    ).eq("id", expired["id"]).execute()

    responses = [
        public(client, t) for t in ("x" * 43, revoked["token"], expired["token"], "y" * 500)
    ]
    assert {r.status_code for r in responses} == {404}
    assert len({r.text for r in responses}) == 1  # byte-for-byte the same answer


def test_the_public_payload_leaks_nothing_it_should_not(client, alice):
    c = make_challenge(client, alice)
    log_today(client, alice, c)
    full = public(client, new_link(client, alice, c, "dashboard")["token"]).json()
    body = json.dumps(full)
    for secret in (alice.email, alice.id, c["id"], *[g["id"] for g in c["goals"]]):
        assert secret not in body, secret
    assert full["display_name"] == alice.email.split("@")[0]
    assert full["dashboard"]["kpis"]["goals_completed"] == 3

    slim = public(client, new_link(client, alice, c, "achievements")["token"]).json()
    assert slim["dashboard"] is None
    assert {"completion", "streaks", "stars", "badges", "challenge_name"} <= set(slim)


def test_links_belong_to_their_owner(client, alice, bob):
    c = make_challenge(client, alice)
    link = new_link(client, alice, c)
    assert (
        client.get(f"{API}/challenges/{c['id']}/share-links", headers=bob.headers).status_code
        == 404
    )
    assert (
        client.post(
            f"{API}/challenges/{c['id']}/share-links",
            headers=bob.headers,
            json={"scope": "dashboard"},
        ).status_code
        == 404
    )
    assert client.delete(f"{API}/share-links/{link['id']}", headers=bob.headers).status_code == 404
    assert public(client, link["token"]).status_code == 200  # bob's attempt did not revoke it


def test_public_endpoint_is_rate_limited(client, alice, monkeypatch):
    monkeypatch.setattr(share_links, "public_limiter", RateLimiter(limit=3, window_s=60))
    codes = [public(client, "z" * 43).status_code for _ in range(5)]
    assert codes == [404, 404, 404, 429, 429]


def test_deleting_the_challenge_kills_its_links(client, alice):
    c = make_challenge(client, alice)
    link = new_link(client, alice, c)
    assert (
        client.delete(f"{API}/challenges/{c['id']}?confirm=true", headers=alice.headers).status_code
        == 204
    )
    assert public(client, link["token"]).status_code == 404


# ---------------------------------------------------------------- friends
def test_friend_request_answer_is_the_same_for_known_and_unknown_emails(client, alice, bob):
    known = client.post(f"{API}/friends/requests", headers=alice.headers, json={"email": bob.email})
    unknown = client.post(
        f"{API}/friends/requests",
        headers=alice.headers,
        json={"email": "nobody-at-all@test.example"},
    )
    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()
    # the sender's own view never reveals which of the two was real
    assert client.get(f"{API}/friends", headers=alice.headers).json() == {
        "friends": [],
        "incoming": [],
    }


def test_cannot_friend_yourself(client, alice):
    r = client.post(
        f"{API}/friends/requests", headers=alice.headers, json={"email": alice.email.upper()}
    )
    assert r.status_code == 400 and r.json()["error"]["code"] == "validation_error"


def test_request_accept_and_duplicates(client, alice, bob):
    for _ in range(3):  # duplicates must not pile up
        client.post(f"{API}/friends/requests", headers=alice.headers, json={"email": bob.email})
    incoming = client.get(f"{API}/friends", headers=bob.headers).json()["incoming"]
    assert len(incoming) == 1 and incoming[0]["display_name"] == alice.email.split("@")[0]

    # only the addressee can answer; the requester gets a 404
    assert (
        client.post(
            f"{API}/friends/requests/{incoming[0]['id']}/accept", headers=alice.headers
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"{API}/friends/requests/{incoming[0]['id']}/accept", headers=bob.headers
        ).status_code
        == 204
    )
    for me, other in ((alice, bob), (bob, alice)):
        listing = client.get(f"{API}/friends", headers=me.headers).json()
        assert [f["user_id"] for f in listing["friends"]] == [other.id] and listing[
            "incoming"
        ] == []


def test_declining_removes_the_request_and_it_can_be_asked_again(client, alice, bob):
    client.post(f"{API}/friends/requests", headers=alice.headers, json={"email": bob.email})
    rid = client.get(f"{API}/friends", headers=bob.headers).json()["incoming"][0]["id"]
    assert (
        client.post(f"{API}/friends/requests/{rid}/decline", headers=bob.headers).status_code == 204
    )
    assert client.get(f"{API}/friends", headers=bob.headers).json()["incoming"] == []
    client.post(f"{API}/friends/requests", headers=alice.headers, json={"email": bob.email})
    assert len(client.get(f"{API}/friends", headers=bob.headers).json()["incoming"]) == 1


def test_asking_someone_who_already_asked_you_is_a_yes(client, alice, bob):
    client.post(f"{API}/friends/requests", headers=alice.headers, json={"email": bob.email})
    client.post(f"{API}/friends/requests", headers=bob.headers, json={"email": alice.email})
    assert len(client.get(f"{API}/friends", headers=alice.headers).json()["friends"]) == 1


# ---------------------------------------------------------------- sharing with a friend
def test_share_requires_friendship_and_gives_a_read_only_view(client, alice, bob):
    c = make_challenge(client, alice)
    log_today(client, alice, c)
    body = {"friend_id": bob.id}

    assert (
        client.post(
            f"{API}/challenges/{c['id']}/shares", headers=alice.headers, json=body
        ).status_code
        == 409
    )
    befriend(client, alice, bob)
    assert (
        client.post(
            f"{API}/challenges/{c['id']}/shares", headers=alice.headers, json=body
        ).status_code
        == 201
    )

    mine = client.get(f"{API}/shared-with-me", headers=bob.headers).json()
    assert [(s["challenge_id"], s["owner_display_name"]) for s in mine] == [
        (c["id"], alice.email.split("@")[0])
    ]

    view = client.get(f"{API}/shared-with-me/{c['id']}/dashboard", headers=bob.headers)
    assert view.status_code == 200
    assert view.json()["dashboard"]["kpis"]["goals_completed"] == 3
    assert alice.email not in view.text and alice.id not in view.text

    # bob can look but not touch: every write route treats him as a stranger
    goal = c["goals"][0]["id"]
    assert client.get(f"{API}/challenges/{c['id']}", headers=bob.headers).status_code == 404
    assert (
        client.patch(
            f"{API}/challenges/{c['id']}", headers=bob.headers, json={"name": "mine now"}
        ).status_code
        == 404
    )
    assert (
        client.put(
            f"{API}/goals/{goal}/entries/{iso(today())}", headers=bob.headers, json={"status": "no"}
        ).status_code
        == 404
    )
    assert client.delete(f"{API}/goals/{goal}?confirm=true", headers=bob.headers).status_code == 404
    assert client.get(f"{API}/challenges/{c['id']}/entries", headers=bob.headers).status_code == 404
    assert (
        client.get(f"{API}/challenges/{c['id']}/dashboard", headers=bob.headers).status_code == 404
    )

    # alice's other challenges stay invisible
    other = make_challenge(client, alice, name="Private")
    assert (
        client.get(f"{API}/shared-with-me/{other['id']}/dashboard", headers=bob.headers).status_code
        == 404
    )

    # unsharing is immediate
    assert (
        client.delete(
            f"{API}/challenges/{c['id']}/shares/{bob.id}", headers=alice.headers
        ).status_code
        == 204
    )
    assert client.get(f"{API}/shared-with-me", headers=bob.headers).json() == []
    assert (
        client.get(f"{API}/shared-with-me/{c['id']}/dashboard", headers=bob.headers).status_code
        == 404
    )


def test_only_the_owner_manages_shares_and_outsiders_see_nothing(client, alice, bob, carol):
    c = make_challenge(client, alice)
    befriend(client, alice, bob)
    client.post(
        f"{API}/challenges/{c['id']}/shares", headers=alice.headers, json={"friend_id": bob.id}
    )
    assert client.get(f"{API}/challenges/{c['id']}/shares", headers=bob.headers).status_code == 404
    assert (
        client.post(
            f"{API}/challenges/{c['id']}/shares", headers=bob.headers, json={"friend_id": carol.id}
        ).status_code
        == 404
    )
    assert (
        client.get(f"{API}/shared-with-me/{c['id']}/dashboard", headers=carol.headers).status_code
        == 404
    )
    assert client.get(f"{API}/shared-with-me", headers=carol.headers).json() == []


def test_unfriending_withdraws_shares_in_both_directions(client, alice, bob):
    mine, theirs = make_challenge(client, alice, name="A"), make_challenge(client, bob, name="B")
    befriend(client, alice, bob)
    client.post(
        f"{API}/challenges/{mine['id']}/shares", headers=alice.headers, json={"friend_id": bob.id}
    )
    client.post(
        f"{API}/challenges/{theirs['id']}/shares", headers=bob.headers, json={"friend_id": alice.id}
    )
    assert (
        client.get(f"{API}/shared-with-me/{mine['id']}/dashboard", headers=bob.headers).status_code
        == 200
    )
    assert (
        client.get(
            f"{API}/shared-with-me/{theirs['id']}/dashboard", headers=alice.headers
        ).status_code
        == 200
    )

    assert client.delete(f"{API}/friends/{bob.id}", headers=alice.headers).status_code == 204
    assert (
        client.get(f"{API}/shared-with-me/{mine['id']}/dashboard", headers=bob.headers).status_code
        == 404
    )
    assert (
        client.get(
            f"{API}/shared-with-me/{theirs['id']}/dashboard", headers=alice.headers
        ).status_code
        == 404
    )
    assert client.get(f"{API}/friends", headers=bob.headers).json()["friends"] == []
    assert client.delete(f"{API}/friends/{bob.id}", headers=alice.headers).status_code == 404


def test_deleting_a_shared_challenge_removes_the_share(client, alice, bob):
    c = make_challenge(client, alice)
    befriend(client, alice, bob)
    client.post(
        f"{API}/challenges/{c['id']}/shares", headers=alice.headers, json={"friend_id": bob.id}
    )
    client.delete(f"{API}/challenges/{c['id']}?confirm=true", headers=alice.headers)
    assert client.get(f"{API}/shared-with-me", headers=bob.headers).json() == []


# ---------------------------------------------------------------- row level security
def test_rls_on_the_sharing_tables(client, alice, bob, carol):
    c = make_challenge(client, alice)
    new_link(client, alice, c)
    befriend(client, alice, bob)
    client.post(
        f"{API}/challenges/{c['id']}/shares", headers=alice.headers, json={"friend_id": bob.id}
    )

    # the people involved can read their rows directly; nobody else can
    assert len(_rest("share_links", alice.token).json()) == 1
    assert _rest("share_links", bob.token).json() == []
    assert (
        len(_rest("friendships", alice.token).json())
        == len(_rest("friendships", bob.token).json())
        == 1
    )
    assert _rest("friendships", carol.token).json() == []
    assert len(_rest("challenge_shares", bob.token).json()) == 1  # shared-with user can select...
    assert _rest("challenge_shares", carol.token).json() == []

    # ...but not write: no policy lets a client insert, update or delete these rows
    forged = {"challenge_id": c["id"], "owner_id": alice.id, "friend_id": carol.id}
    assert _rest("challenge_shares", alice.token, "POST", forged).status_code in (401, 403)
    assert _rest(
        "challenge_shares", bob.token, "POST", {**forged, "owner_id": bob.id}
    ).status_code in (401, 403)
    assert _rest(
        "friendships", carol.token, "POST", {"requester_id": carol.id, "addressee_id": alice.id}
    ).status_code in (401, 403)
    _rest("challenge_shares", bob.token, "DELETE")
    assert len(_rest("challenge_shares", alice.token).json()) == 1  # bob could not remove it

    # anonymous callers get nothing, and the email lookup is not callable by users
    for table in ("share_links", "friendships", "challenge_shares"):
        r = _rest(table)
        assert r.status_code in (401, 403) or r.json() == [], table
    lookup = _rest("rpc/find_user_id_by_email", alice.token, "POST", {"p_email": bob.email})
    assert lookup.status_code in (401, 403, 404) and bob.id not in lookup.text

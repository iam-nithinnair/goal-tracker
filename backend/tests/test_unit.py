"""Fast tests that need no database: date rules, auth token handling, request validation."""

import time
from datetime import UTC, date, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.schemas.models import ChallengeCreate, ProfileUpdate
from app.services.dates import check_entry_date, in_goal_window, is_valid_timezone, today_in

SECRET = "unit-test-secret-which-is-long-enough-32b"


def settings() -> Settings:
    return Settings(supabase_jwt_secret=SECRET, supabase_service_role_key="x")


def token(**over) -> str:
    claims = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "aud": "authenticated",
        "role": "authenticated",
        "email": "a@example.com",
        "exp": int(time.time()) + 600,
        **over,
    }
    return jwt.encode({k: v for k, v in claims.items() if v is not None}, SECRET, algorithm="HS256")


# ---------------------------------------------------------------- dates
def test_today_follows_the_users_timezone_not_the_servers():
    # 23:30 UTC on 1 Nov is already 2 Nov in Kolkata (UTC+5:30), still 1 Nov in New York.
    now = datetime(2026, 11, 1, 23, 30, tzinfo=UTC)
    assert today_in("UTC", now) == date(2026, 11, 1)
    assert today_in("Asia/Kolkata", now) == date(2026, 11, 2)
    assert today_in("America/New_York", now) == date(2026, 11, 1)


def test_today_falls_back_to_utc_for_unknown_zone():
    now = datetime(2026, 11, 1, 23, 30, tzinfo=UTC)
    assert today_in("Nope/Nowhere", now) == date(2026, 11, 1)


def test_naive_now_is_rejected():
    with pytest.raises(ValueError):
        today_in("UTC", datetime(2026, 1, 1))


def test_timezone_validation():
    assert is_valid_timezone("Europe/London")
    assert not is_valid_timezone("Mars/Olympus")
    assert not is_valid_timezone("")


def test_goal_window_is_inclusive_on_both_ends():
    a, b = date(2026, 10, 6), date(2026, 10, 20)
    assert in_goal_window(a, a, b) and in_goal_window(b, a, b)
    assert not in_goal_window(a - timedelta(days=1), a, b)
    assert not in_goal_window(b + timedelta(days=1), a, b)
    assert in_goal_window(date(2030, 1, 1), a, None)  # never retired


BASE = dict(
    today=date(2026, 10, 20),
    challenge_start=date(2026, 10, 6),
    challenge_end=date(2026, 12, 31),
    active_from=date(2026, 10, 6),
    active_to=None,
)


@pytest.mark.parametrize(
    ("day", "expect_error"),
    [
        (date(2026, 10, 20), False),  # today
        (date(2026, 10, 6), False),  # first day of challenge
        (date(2026, 10, 21), True),  # tomorrow
        (date(2026, 10, 5), True),  # before the challenge
        (date(2026, 12, 31), True),  # last day, but in the future
    ],
)
def test_entry_date_boundaries(day, expect_error):
    assert (check_entry_date(day, **BASE) is not None) is expect_error


def test_entry_outside_goal_window_is_rejected():
    msg = check_entry_date(date(2026, 10, 18), **{**BASE, "active_to": date(2026, 10, 15)})
    assert msg is not None and "active" in msg


# ---------------------------------------------------------------- request validation
def test_challenge_rules():
    ok = ChallengeCreate(name="  Winter  ", start_date="2026-10-06", end_date="2026-12-31")
    assert ok.name == "Winter"  # trimmed
    with pytest.raises(ValueError):
        ChallengeCreate(name="", start_date="2026-10-06", end_date="2026-12-31")
    with pytest.raises(ValueError):
        ChallengeCreate(name="x" * 81, start_date="2026-10-06", end_date="2026-12-31")
    with pytest.raises(ValueError):
        ChallengeCreate(name="x", start_date="2026-10-06", end_date="2026-10-05")
    # exactly 366 days is allowed, 367 is not
    ChallengeCreate(name="x", start_date="2026-01-01", end_date="2026-12-31")
    ChallengeCreate(name="leap", start_date="2028-01-01", end_date="2028-12-31")  # 366 days
    with pytest.raises(ValueError):
        ChallengeCreate(name="x", start_date="2028-01-01", end_date="2029-01-01")  # 367 days


def test_profile_update_rules():
    assert ProfileUpdate(timezone="Asia/Kolkata").timezone == "Asia/Kolkata"
    for bad in ({"timezone": "Mars/Olympus"}, {"avatar_color": "red"}, {"display_name": " "}):
        with pytest.raises(ValueError):
            ProfileUpdate(**bad)
    # role can never be set through this model
    assert "role" not in ProfileUpdate.model_fields


# ---------------------------------------------------------------- auth + error shape
@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr("app.core.auth.get_settings", settings, raising=False)
    app = create_app()
    from app.core.config import get_settings

    app.dependency_overrides[get_settings] = settings
    return TestClient(app)


def test_health_is_public(client):
    assert client.get("/health").json() == {"status": "ok"}


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": "Bearer not-a-jwt"},
        {"Authorization": f"Bearer {token(exp=int(time.time()) - 10)}"},  # expired
        {"Authorization": f"Bearer {token(aud='someone-else')}"},  # wrong audience
        {"Authorization": f"Bearer {token(role='anon')}"},  # not an authenticated user
        {"Authorization": f"Bearer {token()[:-3]}abc"},  # tampered signature
        {"Authorization": f"Token {token()}"},  # wrong scheme
    ],
)
def test_bad_tokens_get_401_with_the_standard_error_shape(client, headers):
    res = client.get("/api/v1/me", headers=headers)
    assert res.status_code == 401
    body = res.json()
    assert body["error"]["code"] == "unauthorized"
    assert "message" in body["error"]


def test_unknown_route_uses_error_shape(client):
    res = client.get("/api/v1/nope")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "not_found"

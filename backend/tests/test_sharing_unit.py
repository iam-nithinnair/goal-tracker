"""Share-token and rate-limit helpers, and request validation. No database."""

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.schemas.sharing import FriendRequestIn, ShareLinkCreate
from app.services.sharing import RateLimiter, hash_token, new_token


def test_tokens_are_long_unique_and_url_safe():
    tokens = {new_token() for _ in range(200)}
    assert len(tokens) == 200
    for t in tokens:
        assert len(t) >= 43  # 32 random bytes = 256 bits
        assert t.replace("-", "").replace("_", "").isalnum()


def test_only_a_hash_of_the_token_is_kept():
    t = new_token()
    h = hash_token(t)
    assert h != t and t not in h
    assert h == hash_token(t) and len(h) == 64
    assert hash_token(t + "x") != h


def test_rate_limiter_blocks_after_the_limit_and_recovers():
    now = [0.0]
    rl = RateLimiter(limit=3, window_s=60, clock=lambda: now[0])
    assert [rl.allow("a") for _ in range(4)] == [True, True, True, False]
    assert rl.allow("b")  # other clients are unaffected
    now[0] = 61
    assert rl.allow("a")  # the window has passed


def test_expiry_must_be_in_the_future():
    soon = datetime.now(UTC) + timedelta(days=1)
    assert ShareLinkCreate(scope="dashboard", expires_at=soon).expires_at == soon
    assert ShareLinkCreate(scope="achievements").expires_at is None
    with pytest.raises(ValidationError):
        ShareLinkCreate(scope="dashboard", expires_at=datetime.now(UTC) - timedelta(minutes=1))
    with pytest.raises(ValidationError):
        ShareLinkCreate(scope="everything")


@pytest.mark.parametrize("bad", ["", "nope", "a@b", "a b@c.com", "@c.com"])
def test_friend_request_needs_an_email_address(bad):
    with pytest.raises(ValidationError):
        FriendRequestIn(email=bad)


def test_friend_request_email_is_normalised():
    assert FriendRequestIn(email="  Bob@Example.COM ").email == "bob@example.com"

"""The hosted Supabase project signs tokens with ES256 (asymmetric keys), so the backend must verify
them through the JWKS endpoint instead of a shared secret. These tests exercise that branch with a
locally generated P-256 key (no network)."""

import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from app.core import auth
from app.core.config import Settings, get_settings
from app.main import create_app

KID = "test-key-1"


class FakeJwks:
    def __init__(self, public_key):
        self.public_key = public_key

    def get_signing_key_from_jwt(self, _token):
        return type("SigningKey", (), {"key": self.public_key})()


def make_token(private_key, *, alg="ES256", **over) -> str:
    claims = {
        "sub": "22222222-2222-2222-2222-222222222222",
        "aud": "authenticated",
        "role": "authenticated",
        "email": "hosted@example.com",
        "exp": int(time.time()) + 600,
        **over,
    }
    return jwt.encode(claims, private_key, algorithm=alg, headers={"kid": KID})


@pytest.fixture
def keys():
    return ec.generate_private_key(ec.SECP256R1()), ec.generate_private_key(ec.SECP256R1())


def decode(token, public_key, monkeypatch):
    monkeypatch.setattr(auth, "_jwks_client", lambda _url: FakeJwks(public_key))
    # no shared secret configured, exactly like a hosted project using asymmetric keys
    return auth.decode_token(token, Settings(supabase_url="https://example.supabase.co"))


def test_valid_es256_token_is_accepted_without_any_shared_secret(keys, monkeypatch):
    private, _ = keys
    claims = decode(make_token(private), private.public_key(), monkeypatch)
    assert claims["sub"] == "22222222-2222-2222-2222-222222222222"


def test_token_signed_by_another_key_is_rejected(keys, monkeypatch):
    mine, attacker = keys
    with pytest.raises(Exception) as exc:
        decode(make_token(attacker), mine.public_key(), monkeypatch)
    assert getattr(exc.value, "status_code", None) == 401


@pytest.mark.parametrize("over", [{"exp": int(time.time()) - 5}, {"aud": "other"}])
def test_expired_or_wrong_audience_es256_tokens_are_rejected(keys, monkeypatch, over):
    private, _ = keys
    with pytest.raises(Exception) as exc:
        decode(make_token(private, **over), private.public_key(), monkeypatch)
    assert getattr(exc.value, "status_code", None) == 401


def test_hs256_token_is_refused_when_no_secret_is_configured(monkeypatch):
    # An attacker must not be able to downgrade a JWKS-only project to a guessable HS256 secret.
    forged = jwt.encode(
        {"sub": "x", "aud": "authenticated", "role": "authenticated", "exp": int(time.time()) + 60},
        "guessable",
        algorithm="HS256",
    )
    with pytest.raises(Exception) as exc:
        auth.decode_token(forged, Settings(supabase_url="https://example.supabase.co"))
    assert getattr(exc.value, "status_code", None) == 401


def test_endpoint_accepts_es256_bearer_token(keys, monkeypatch):
    private, _ = keys
    monkeypatch.setattr(auth, "_jwks_client", lambda _url: FakeJwks(private.public_key()))
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        supabase_url="https://example.supabase.co", supabase_service_role_key="x"
    )
    client = TestClient(app)
    # The token is valid, so auth passes and the request moves on to the profile lookup (which needs
    # a database). Reaching that step instead of a 401 proves the ES256 path works end to end.
    monkeypatch.setattr(
        "app.deps.get_client", lambda: (_ for _ in ()).throw(RuntimeError("db reached"))
    )
    with pytest.raises(RuntimeError, match="db reached"):
        client.get("/api/v1/me", headers={"Authorization": f"Bearer {make_token(private)}"})

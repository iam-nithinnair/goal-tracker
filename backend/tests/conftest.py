"""Integration fixtures: real users, real tokens, real local Supabase (`supabase start`).

Tests marked `integration` are skipped automatically when the stack isn't running."""

import os
import uuid
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


def _is_local(url: str) -> bool:
    host = urlparse(url).hostname or ""
    return host in {"127.0.0.1", "localhost", "::1", "host.docker.internal"}


def _stack_up() -> bool:
    try:
        httpx.get(f"{get_settings().supabase_url}/auth/v1/health", timeout=2)
        return True
    except httpx.HTTPError:
        return False


def pytest_collection_modifyitems(config, items):
    """Integration tests create (fake) users and data, so they only run against a LOCAL stack.
    They are refused for any hosted project unless ALLOW_REMOTE_TESTS=1 is set deliberately."""
    url = get_settings().supabase_url
    if not _is_local(url) and os.environ.get("ALLOW_REMOTE_TESTS") != "1":
        reason = f"SUPABASE_URL ({url}) is not local; refusing to create test users there"
    elif not _stack_up():
        reason = "local Supabase isn't running (run `npx supabase start`)"
    else:
        return
    skip = pytest.mark.skip(reason=reason)
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip)


@dataclass
class User:
    id: str
    email: str
    token: str

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}


def _create_user(label: str) -> User:
    s = get_settings()
    email = f"{label}-{uuid.uuid4().hex[:8]}@test.example"
    password = "correct-horse-battery"
    admin = {
        "apikey": s.supabase_service_role_key,
        "Authorization": f"Bearer {s.supabase_service_role_key}",
    }
    r = httpx.post(
        f"{s.supabase_url}/auth/v1/admin/users",
        headers=admin,
        json={"email": email, "password": password, "email_confirm": True},
        timeout=20,
    )
    r.raise_for_status()
    user_id = r.json()["id"]
    t = httpx.post(
        f"{s.supabase_url}/auth/v1/token?grant_type=password",
        headers={"apikey": s.supabase_anon_key},
        json={"email": email, "password": password},
        timeout=20,
    )
    t.raise_for_status()
    return User(id=user_id, email=email, token=t.json()["access_token"])


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def alice() -> User:
    return _create_user("alice")


@pytest.fixture
def bob() -> User:
    return _create_user("bob")


@pytest.fixture
def carol() -> User:
    return _create_user("carol")

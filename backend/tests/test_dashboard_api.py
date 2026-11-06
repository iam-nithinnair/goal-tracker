"""GET /challenges/{id}/dashboard: shape, ownership and the `from` alias (fake repo, no DB)."""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.deps import get_profile, get_repo
from app.main import create_app

USER = "11111111-1111-1111-1111-111111111111"
CHALLENGE = "22222222-2222-2222-2222-222222222222"
GOAL = "33333333-3333-3333-3333-333333333333"


class FakeRepo:
    def get_challenge(self, owner_id, challenge_id):
        if owner_id != USER or challenge_id != CHALLENGE:
            return None  # someone else's (or missing) challenge looks the same
        start = date.today() - timedelta(days=3)
        return {
            "id": CHALLENGE,
            "start_date": start.isoformat(),
            "end_date": (start + timedelta(days=20)).isoformat(),
            "goals": [
                {
                    "id": GOAL,
                    "name": "Read",
                    "active_from": start.isoformat(),
                    "active_to": None,
                    "position": 1,
                }
            ],
        }

    def list_entries(self, challenge_id, start, end):
        first = date.today() - timedelta(days=3)
        return [{"goal_id": GOAL, "entry_date": first.isoformat(), "status": "yes"}]


@pytest.fixture
def client():
    app = create_app()
    app.dependency_overrides[get_profile] = lambda: {"id": USER, "timezone": "UTC"}
    app.dependency_overrides[get_repo] = lambda: FakeRepo()
    return TestClient(app)


def test_dashboard_shape(client):
    r = client.get(f"/api/v1/challenges/{CHALLENGE}/dashboard")
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {
        "as_of",
        "kpis",
        "streaks",
        "goals",
        "months",
        "goal_months",
        "weeks",
        "days",
    }
    assert body["kpis"]["goals_completed"] == 1
    assert body["goals"][0]["name"] == "Read"
    assert set(body["weeks"][0]) == {"week", "from", "to", "done", "possible", "completion"}


def test_another_users_challenge_is_a_404(client):
    other = "44444444-4444-4444-4444-444444444444"
    assert client.get(f"/api/v1/challenges/{other}/dashboard").status_code == 404
    client.app.dependency_overrides[get_profile] = lambda: {"id": "someone-else", "timezone": "UTC"}
    assert client.get(f"/api/v1/challenges/{CHALLENGE}/dashboard").status_code == 404

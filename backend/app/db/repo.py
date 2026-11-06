"""Data access. Uses the Supabase service-role client, which bypasses Row Level Security,
so EVERY query here must be scoped to the caller (owner_id) itself. RLS stays enabled as a
second line of defence for any direct access (see docs/02-architecture.md)."""

from datetime import UTC, date, datetime
from functools import lru_cache
from typing import Any

from supabase import Client, create_client

from app.core.config import get_settings


@lru_cache
def get_client() -> Client:
    s = get_settings()
    return create_client(s.supabase_url, s.supabase_service_role_key)


def _iso(d: date | None) -> str | None:
    return d.isoformat() if d else None


class Repo:
    def __init__(self, client: Client):
        self.db = client

    # ------------------------------------------------------------ profiles
    def get_profile(self, user_id: str) -> dict | None:
        rows = self.db.table("profiles").select("*").eq("id", user_id).limit(1).execute().data
        return rows[0] if rows else None

    def update_profile(self, user_id: str, fields: dict[str, Any]) -> dict | None:
        if fields:
            self.db.table("profiles").update(fields).eq("id", user_id).execute()
        return self.get_profile(user_id)

    # ------------------------------------------------------------ templates
    def list_templates(self) -> list[dict]:
        rows = (
            self.db.table("challenges")
            .select("*, goals(*)")
            .eq("is_template", True)
            .order("name")
            .execute()
            .data
        )
        for r in rows:
            r["goals"] = sorted(r["goals"], key=lambda g: g["position"])
        return rows

    def get_template(self, template_id: str) -> dict | None:
        rows = (
            self.db.table("challenges")
            .select("*, goals(*)")
            .eq("id", template_id)
            .eq("is_template", True)
            .limit(1)
            .execute()
            .data
        )
        if not rows:
            return None
        rows[0]["goals"] = sorted(rows[0]["goals"], key=lambda g: g["position"])
        return rows[0]

    # ------------------------------------------------------------ challenges
    def list_challenges(self, owner_id: str, status: str | None = None) -> list[dict]:
        q = self.db.table("challenges").select("*").eq("owner_id", owner_id)
        if status:
            q = q.eq("status", status)
        return q.order("start_date", desc=True).execute().data

    def get_challenge(self, owner_id: str, challenge_id: str) -> dict | None:
        rows = (
            self.db.table("challenges")
            .select("*, goals(*)")
            .eq("id", challenge_id)
            .eq("owner_id", owner_id)
            .limit(1)
            .execute()
            .data
        )
        if not rows:
            return None
        rows[0]["goals"] = sorted(rows[0]["goals"], key=lambda g: g["position"])
        return rows[0]

    def create_challenge(
        self, owner_id: str, name: str, start: date, end: date, goal_names: list[str]
    ) -> dict:
        created = (
            self.db.table("challenges")
            .insert(
                {
                    "owner_id": owner_id,
                    "name": name,
                    "start_date": _iso(start),
                    "end_date": _iso(end),
                }
            )
            .execute()
            .data[0]
        )
        if goal_names:
            self.db.table("goals").insert(
                [
                    {
                        "challenge_id": created["id"],
                        "name": g,
                        "position": i + 1,
                        "active_from": _iso(start),
                    }
                    for i, g in enumerate(goal_names)
                ]
            ).execute()
        return self.get_challenge(owner_id, created["id"])  # type: ignore[return-value]

    def update_challenge(self, challenge_id: str, fields: dict[str, Any]) -> None:
        if fields:
            self.db.table("challenges").update(fields).eq("id", challenge_id).execute()

    def delete_challenge(self, challenge_id: str) -> None:
        self.db.table("challenges").delete().eq("id", challenge_id).execute()

    def entry_date_bounds(self, challenge_id: str) -> tuple[date | None, date | None]:
        """Earliest and latest logged entry date in a challenge."""
        base = (
            self.db.table("daily_entries")
            .select("entry_date, goals!inner(challenge_id)")
            .eq("goals.challenge_id", challenge_id)
        )
        first = base.order("entry_date").limit(1).execute().data
        last = (
            self.db.table("daily_entries")
            .select("entry_date, goals!inner(challenge_id)")
            .eq("goals.challenge_id", challenge_id)
            .order("entry_date", desc=True)
            .limit(1)
            .execute()
            .data
        )
        return (
            date.fromisoformat(first[0]["entry_date"]) if first else None,
            date.fromisoformat(last[0]["entry_date"]) if last else None,
        )

    def realign_goals_to_dates(
        self, challenge_id: str, old_start: date, new_start: date, new_end: date
    ) -> None:
        """Keep goal windows inside the challenge after its dates change."""
        goals = self.db.table("goals").select("*").eq("challenge_id", challenge_id).execute().data
        for g in goals:
            patch: dict[str, Any] = {}
            active_from = date.fromisoformat(g["active_from"])
            if active_from == old_start or active_from < new_start:
                patch["active_from"] = _iso(new_start)
            if g["active_to"] and date.fromisoformat(g["active_to"]) > new_end:
                patch["active_to"] = _iso(new_end)
            if patch:
                self.db.table("goals").update(patch).eq("id", g["id"]).execute()

    # ------------------------------------------------------------ goals
    def get_goal(self, owner_id: str, goal_id: str) -> dict | None:
        """A goal plus its challenge's dates, only if the caller owns it."""
        rows = (
            self.db.table("goals")
            .select("*, challenges!inner(id, owner_id, start_date, end_date)")
            .eq("id", goal_id)
            .eq("challenges.owner_id", owner_id)
            .limit(1)
            .execute()
            .data
        )
        return rows[0] if rows else None

    def add_goal(self, challenge: dict, name: str, position: int | None) -> dict:
        existing = challenge["goals"]
        end_pos = max((g["position"] for g in existing), default=0) + 1
        pos = end_pos if position is None else position
        if position is not None:
            # make room: shift goals at or after the requested position
            for g in existing:
                if g["position"] >= pos:
                    self.db.table("goals").update({"position": g["position"] + 1}).eq(
                        "id", g["id"]
                    ).execute()
        return (
            self.db.table("goals")
            .insert(
                {
                    "challenge_id": challenge["id"],
                    "name": name,
                    "position": pos,
                    "active_from": challenge["start_date"],
                }
            )
            .execute()
            .data[0]
        )

    def update_goal(self, goal_id: str, fields: dict[str, Any]) -> dict:
        if fields:
            self.db.table("goals").update(fields).eq("id", goal_id).execute()
        return self.db.table("goals").select("*").eq("id", goal_id).limit(1).execute().data[0]

    def reorder_goals(self, goal_ids: list[str]) -> None:
        for i, gid in enumerate(goal_ids):
            self.db.table("goals").update({"position": i + 1}).eq("id", gid).execute()

    def delete_goal(self, goal_id: str) -> None:
        self.db.table("goals").delete().eq("id", goal_id).execute()

    # ------------------------------------------------------------ entries
    def list_entries(self, challenge_id: str, start: date | None, end: date | None) -> list[dict]:
        q = (
            self.db.table("daily_entries")
            .select("goal_id, entry_date, status, goals!inner(challenge_id)")
            .eq("goals.challenge_id", challenge_id)
        )
        if start:
            q = q.gte("entry_date", _iso(start))
        if end:
            q = q.lte("entry_date", _iso(end))
        rows = q.order("entry_date").limit(20000).execute().data
        return [{k: r[k] for k in ("goal_id", "entry_date", "status")} for r in rows]

    def upsert_entries(self, rows: list[dict]) -> list[dict]:
        out = (
            self.db.table("daily_entries")
            .upsert(rows, on_conflict="goal_id,entry_date")
            .execute()
            .data
        )
        return [{k: r[k] for k in ("goal_id", "entry_date", "status")} for r in out]

    def delete_entry(self, goal_id: str, day: date) -> None:
        (
            self.db.table("daily_entries")
            .delete()
            .eq("goal_id", goal_id)
            .eq("entry_date", _iso(day))
            .execute()
        )

    # ------------------------------------------------------------ awards
    def list_badges(self) -> list[dict]:
        return (
            self.db.table("badges")
            .select("*")
            .eq("is_active", True)
            .order("sort_order")
            .execute()
            .data
        )

    def earned_badges(self, user_id: str, challenge_id: str | None = None) -> list[dict]:
        q = (
            self.db.table("user_badges")
            .select("badge_code, challenge_id, earned_on, challenges(name)")
            .eq("user_id", user_id)
        )
        if challenge_id:
            q = q.eq("challenge_id", challenge_id)
        return q.order("earned_on").execute().data

    def award_badges(
        self, user_id: str, challenge_id: str, codes: list[str], earned_on: date
    ) -> list[str]:
        """Record badges, ignoring any already held; returns only the codes that are NEW."""
        if not codes:
            return []
        rows = [
            {
                "user_id": user_id,
                "badge_code": c,
                "challenge_id": challenge_id,
                "earned_on": _iso(earned_on),
            }
            for c in codes
        ]
        out = (
            self.db.table("user_badges")
            .upsert(rows, on_conflict="user_id,badge_code,challenge_id", ignore_duplicates=True)
            .execute()
            .data
        )
        return [r["badge_code"] for r in out]

    def active_challenges_with_owners(self) -> list[dict]:
        """Every live, non-template challenge with its owner's timezone (for the nightly job)."""
        return (
            self.db.table("challenges")
            .select("*, goals(*), profiles!challenges_owner_id_fkey(id, timezone, is_disabled)")
            .eq("is_template", False)
            .eq("status", "active")
            .execute()
            .data
        )

    # ------------------------------------------------------------ sharing: public links
    def create_share_link(
        self,
        owner_id: str,
        challenge_id: str,
        scope: str,
        expires_at: str | None,
        token_hash: str,
    ) -> dict:
        return (
            self.db.table("share_links")
            .insert(
                {
                    "owner_id": owner_id,
                    "challenge_id": challenge_id,
                    "scope": scope,
                    "expires_at": expires_at,
                    "token_hash": token_hash,
                }
            )
            .execute()
            .data[0]
        )

    def list_share_links(self, challenge_id: str) -> list[dict]:
        return (
            self.db.table("share_links")
            .select("id, scope, created_at, expires_at, revoked_at")
            .eq("challenge_id", challenge_id)
            .order("created_at", desc=True)
            .execute()
            .data
        )

    def revoke_share_link(self, owner_id: str, link_id: str) -> bool:
        """Revoke (immediately) a link the caller owns; False when it is not theirs or missing."""
        rows = (
            self.db.table("share_links")
            .update({"revoked_at": datetime.now(UTC).isoformat()})
            .eq("id", link_id)
            .eq("owner_id", owner_id)
            .execute()
            .data
        )
        return bool(rows)

    def get_share_link_by_hash(self, token_hash: str) -> dict | None:
        rows = (
            self.db.table("share_links").select("*").eq("token_hash", token_hash).limit(1).execute()
        ).data
        return rows[0] if rows else None

    def get_challenge_by_id(self, challenge_id: str) -> dict | None:
        """A challenge with its goals, with NO ownership check: only call after access was proven
        some other way (a valid share link, or a share row for the caller)."""
        rows = (
            self.db.table("challenges")
            .select("*, goals(*)")
            .eq("id", challenge_id)
            .eq("is_template", False)
            .limit(1)
            .execute()
            .data
        )
        if not rows:
            return None
        rows[0]["goals"] = sorted(rows[0]["goals"], key=lambda g: g["position"])
        return rows[0]

    # ------------------------------------------------------------ sharing: friends
    def find_user_id_by_email(self, email: str) -> str | None:
        return self.db.rpc("find_user_id_by_email", {"p_email": email}).execute().data or None

    def friendship_between(self, a: str, b: str) -> dict | None:
        rows = (
            self.db.table("friendships")
            .select("*")
            .or_(
                f"and(requester_id.eq.{a},addressee_id.eq.{b}),"
                f"and(requester_id.eq.{b},addressee_id.eq.{a})"
            )
            .limit(1)
            .execute()
            .data
        )
        return rows[0] if rows else None

    def create_friend_request(self, requester_id: str, addressee_id: str) -> None:
        self.db.table("friendships").insert(
            {"requester_id": requester_id, "addressee_id": addressee_id}
        ).execute()

    def get_friendship(self, friendship_id: str) -> dict | None:
        rows = self.db.table("friendships").select("*").eq("id", friendship_id).limit(1).execute()
        return rows.data[0] if rows.data else None

    def accept_friendship(self, friendship_id: str) -> None:
        self.db.table("friendships").update(
            {"status": "accepted", "responded_at": datetime.now(UTC).isoformat()}
        ).eq("id", friendship_id).execute()

    def delete_friendship(self, friendship_id: str) -> None:
        self.db.table("friendships").delete().eq("id", friendship_id).execute()

    def list_friendships(self, user_id: str) -> list[dict]:
        return (
            self.db.table("friendships")
            .select("*")
            .or_(f"requester_id.eq.{user_id},addressee_id.eq.{user_id}")
            .order("created_at", desc=True)
            .execute()
            .data
        )

    def profiles_by_ids(self, ids: list[str]) -> dict[str, dict]:
        if not ids:
            return {}
        rows = self.db.table("profiles").select("id, display_name").in_("id", ids).execute().data
        return {r["id"]: r for r in rows}

    # ------------------------------------------------------------ sharing: with a friend
    def create_share(self, challenge_id: str, owner_id: str, friend_id: str) -> None:
        self.db.table("challenge_shares").upsert(
            {"challenge_id": challenge_id, "owner_id": owner_id, "friend_id": friend_id},
            on_conflict="challenge_id,friend_id",
            ignore_duplicates=True,
        ).execute()

    def delete_share(self, challenge_id: str, friend_id: str) -> None:
        (
            self.db.table("challenge_shares")
            .delete()
            .eq("challenge_id", challenge_id)
            .eq("friend_id", friend_id)
            .execute()
        )

    def delete_shares_between(self, a: str, b: str) -> None:
        """Drop every challenge share in either direction between two users."""
        for owner, friend in ((a, b), (b, a)):
            (
                self.db.table("challenge_shares")
                .delete()
                .eq("owner_id", owner)
                .eq("friend_id", friend)
                .execute()
            )

    def list_shares(self, challenge_id: str) -> list[dict]:
        return (
            self.db.table("challenge_shares")
            .select("friend_id, created_at")
            .eq("challenge_id", challenge_id)
            .execute()
            .data
        )

    def get_share(self, challenge_id: str, friend_id: str) -> dict | None:
        rows = (
            self.db.table("challenge_shares")
            .select("*")
            .eq("challenge_id", challenge_id)
            .eq("friend_id", friend_id)
            .limit(1)
            .execute()
            .data
        )
        return rows[0] if rows else None

    def list_shared_with(self, friend_id: str) -> list[dict]:
        return (
            self.db.table("challenge_shares")
            .select("owner_id, created_at, challenges(id, name, start_date, end_date, status)")
            .eq("friend_id", friend_id)
            .order("created_at", desc=True)
            .execute()
            .data
        )

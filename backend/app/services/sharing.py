"""Share-link tokens and the public-endpoint rate limiter."""

import hashlib
import secrets
import time
from collections import defaultdict, deque
from collections.abc import Callable


def new_token() -> str:
    """256 bits from the OS CSPRNG, URL-safe. Shown to the owner once and never stored."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """What the database keeps. The token is high-entropy, so a plain SHA-256 is enough."""
    return hashlib.sha256(token.encode()).hexdigest()


class RateLimiter:
    """Sliding window per key, in memory. Fine for a single instance; a shared store would be
    needed to scale out (noted in docs/08-deploy.md)."""

    def __init__(
        self, limit: int, window_s: float, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self.limit, self.window_s, self.clock = limit, window_s, clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = self.clock()
        hits = self._hits[key]
        while hits and now - hits[0] >= self.window_s:
            hits.popleft()
        if len(hits) >= self.limit:
            return False
        hits.append(now)
        return True

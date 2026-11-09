"""In-memory rate limiting: token buckets and an hourly token budget

A `dict` rather than Redis: the API runs as a single process. With several
workers each would keep its own counters and the limits would multiply.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field


@dataclass
class _Bucket:
    """How many tokens one key has left and when it was last touched"""

    tokens: float
    updated_at: float


@dataclass
class TokenBucket:
    """Allows `capacity` requests at once then refills at `refill_per_second`"""

    capacity: float
    refill_per_second: float
    _buckets: dict[str, _Bucket] = field(default_factory=dict)

    def consume(self, key: str, cost: float = 1.0) -> bool:
        """Takes one token for this key"""
        now = time.monotonic()
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = _Bucket(tokens=self.capacity, updated_at=now)
            self._buckets[key] = bucket

        elapsed = now - bucket.updated_at
        bucket.tokens = min(self.capacity, bucket.tokens + elapsed * self.refill_per_second)
        bucket.updated_at = now

        if bucket.tokens < cost:
            return False
        bucket.tokens -= cost
        return True

    def retry_after(self, key: str, cost: float = 1.0) -> int:
        """Seconds to wait before the next try is allowed"""
        bucket = self._buckets.get(key)
        if bucket is None or bucket.tokens >= cost:
            return 0
        return int((cost - bucket.tokens) / self.refill_per_second) + 1

    def prune(self, max_age: float = 3600.0) -> None:
        """Drops keys nobody has touched in a while

        Without it the dict grows by one entry per IP forever
        which is a slow memory leak an attacker can drive on purpose
        """
        cutoff = time.monotonic() - max_age
        for key in [k for k, b in self._buckets.items() if b.updated_at < cutoff]:
            del self._buckets[key]


@dataclass
class TokenBudget:
    """Count tokens in a sliding hour window

    Counts what the engine reports (prompt + output tokens) after each call,
    because a request counter cannot tell a two-line answer from a page.
    Shared by every student; one process only, like the buckets above.
    """

    per_hour: int
    _spent: deque[tuple[float, int]] = field(default_factory=deque)
    _total: int = field(default=0)

    def available(self) -> bool:
        """Whether the budget has tokens left"""
        now = time.monotonic()
        cutoff = now - 3600
        while self._spent and self._spent[0][0] < cutoff:
            _, tokens = self._spent.popleft()
            self._total -= tokens
        return self._total < self.per_hour

    def spend(self, tokens: int) -> None:
        """Record tokens spent"""
        now = time.monotonic()
        self._spent.append((now, tokens))
        self._total += tokens

    def clear(self) -> None:
        """Clear all spent tokens"""
        self._spent.clear()
        self._total = 0


# 5 consecutive tries then 1 every 12 s (~5/min)
login_limiter = TokenBucket(capacity=5, refill_per_second=1 / 12)
# Sign-up costs one full Argon2 hash, so stricter
register_limiter = TokenBucket(capacity=3, refill_per_second=1 / 60)
# 2FA: a 6-digit code has only 10^6 values, so guessing must stay slow
totp_limiter = TokenBucket(capacity=5, refill_per_second=1 / 30)
# Chat : keyed by sender id, not IP. 20 messages back to back then 1/s —
# comfortable for a real conversation, a wall against a flood loop.
message_limiter = TokenBucket(capacity=20, refill_per_second=1)
# Grading : keyed by student id. 5 answers back to back then 1 every 20 s —
# the per-student guard in front of the shared token budget.
grading_limiter = TokenBucket(capacity=5, refill_per_second=1 / 20)

oauth_limiter = TokenBucket(capacity=10, refill_per_second=1 / 30)

"""In-memory AI-specific controls: users, sliding-window rate limit, daily token quota.
Swap for Redis/Postgres in production (see docs/ARCHITECTURE.md)."""

import time
from collections import defaultdict, deque
from datetime import UTC, datetime


class UserStore:
    def __init__(self) -> None:
        self._users: dict[str, str] = {}

    def add(self, username: str, password_hash: str) -> bool:
        if username in self._users:
            return False
        self._users[username] = password_hash
        return True

    def get_hash(self, username: str) -> str | None:
        return self._users.get(username)

    def exists(self, username: str) -> bool:
        return username in self._users


class RateLimiter:
    def __init__(self, per_minute: int) -> None:
        self.per_minute = per_minute
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def _prune(self, user: str) -> deque[float]:
        q = self._hits[user]
        while q and q[0] < time.monotonic() - 60:
            q.popleft()
        return q

    def check(self, user: str) -> int | None:
        """Returns None if allowed, else seconds until retry."""
        q = self._prune(user)
        if len(q) >= self.per_minute:
            return max(1, int(60 - (time.monotonic() - q[0])))
        q.append(time.monotonic())
        return None

    def current(self, user: str) -> int:
        return len(self._prune(user))


class UsageMeter:
    def __init__(self, daily_quota: int) -> None:
        self.daily_quota = daily_quota
        self._used: dict[tuple[str, str], int] = defaultdict(int)

    @staticmethod
    def _day() -> str:
        return datetime.now(UTC).strftime("%Y-%m-%d")

    def used(self, user: str) -> int:
        return self._used[(user, self._day())]

    def over_quota(self, user: str) -> bool:
        return self.used(user) >= self.daily_quota

    def add(self, user: str, tokens: int) -> None:
        self._used[(user, self._day())] += tokens

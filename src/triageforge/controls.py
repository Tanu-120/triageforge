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


class FeedbackStore:
    """In-memory analyst feedback on triage quality (demo / assignment)."""

    def __init__(self) -> None:
        self._items: list[dict[str, object]] = []

    def add(self, username: str, ticket_id: str, helpful: bool, note: str | None) -> None:
        self._items.append(
            {
                "username": username,
                "ticket_id": ticket_id,
                "helpful": helpful,
                "note": note,
                "at": datetime.now(UTC).isoformat(),
            }
        )

    def count(self, username: str | None = None) -> int:
        if username is None:
            return len(self._items)
        return sum(1 for i in self._items if i["username"] == username)

    def helpful_rate(self, username: str) -> float | None:
        mine = [i for i in self._items if i["username"] == username]
        if not mine:
            return None
        return sum(1 for i in mine if i["helpful"]) / len(mine)


class HistoryStore:
    """Per-user triage history for sidebar + dashboard (in-memory demo store)."""

    def __init__(self, max_per_user: int = 50) -> None:
        self._max = max_per_user
        self._items: dict[str, list[dict[str, object]]] = defaultdict(list)

    def add(self, username: str, preview: str, result: dict[str, object]) -> dict[str, object]:
        item: dict[str, object] = {
            "ticket_id": str(result.get("ticket_id", "")),
            "preview": preview[:140],
            "pinned": False,
            "created_at": datetime.now(UTC).isoformat(),
            "result": result,
        }
        bucket = self._items[username]
        bucket.insert(0, item)
        del bucket[self._max :]
        return item

    def list(self, username: str) -> list[dict[str, object]]:
        return list(self._items.get(username, []))

    def get(self, username: str, ticket_id: str) -> dict[str, object] | None:
        for item in self._items.get(username, []):
            if item["ticket_id"] == ticket_id:
                return item
        return None

    def delete(self, username: str, ticket_id: str) -> bool:
        bucket = self._items.get(username, [])
        before = len(bucket)
        self._items[username] = [i for i in bucket if i["ticket_id"] != ticket_id]
        return len(self._items[username]) < before

    def toggle_pin(self, username: str, ticket_id: str) -> dict[str, object] | None:
        item = self.get(username, ticket_id)
        if item is None:
            return None
        item["pinned"] = not bool(item["pinned"])
        bucket = self._items[username]
        pinned = [i for i in bucket if i["pinned"]]
        rest = [i for i in bucket if not i["pinned"]]
        self._items[username] = pinned + rest
        return item

    def clear(self, username: str) -> int:
        n = len(self._items.get(username, []))
        self._items[username] = []
        return n

    def stats(self, username: str) -> dict[str, int | float | dict[str, int]]:
        items = self._items.get(username, [])
        by_category: dict[str, int] = defaultdict(int)
        by_priority: dict[str, int] = defaultdict(int)
        by_queue: dict[str, int] = defaultdict(int)
        escalations = 0
        severity_sum = 0
        for item in items:
            result = item["result"]
            assert isinstance(result, dict)
            cat = str(result.get("category", "other"))
            pri = str(result.get("priority", "medium"))
            queue = str(result.get("assigned_queue", "general_support"))
            by_category[cat] += 1
            by_priority[pri] += 1
            by_queue[queue] += 1
            if result.get("escalation_required"):
                escalations += 1
            severity_sum += int(result.get("severity_score", 0) or 0)
        total = len(items)
        return {
            "total_tickets": total,
            "escalations": escalations,
            "avg_severity": round(severity_sum / total, 2) if total else 0.0,
            "by_category": dict(sorted(by_category.items(), key=lambda kv: (-kv[1], kv[0]))),
            "by_priority": dict(by_priority),
            "by_queue": dict(sorted(by_queue.items(), key=lambda kv: (-kv[1], kv[0]))),
            "pinned": sum(1 for i in items if i["pinned"]),
        }

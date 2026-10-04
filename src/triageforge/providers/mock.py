import json
from typing import Any

from .base import ProviderResult


class MockProvider:
    """Deterministic keyword model for tests, CI and offline demos."""

    name = "mock"

    async def generate_json(
        self, system: str, user: str, json_schema: dict[str, Any]
    ) -> ProviderResult:
        t = user.lower()
        cat = "other"
        for kw, c in [
            ("refund", "billing"),
            ("charge", "billing"),
            ("invoice", "billing"),
            ("crash", "bug"),
            ("error", "bug"),
            ("password", "account"),
            ("login", "account"),
            ("would be great", "feature_request"),
        ]:
            if kw in t:
                cat = c
                break
        urgent = any(w in t for w in ("asap", "urgent", "down", "outage"))
        neg = any(w in t for w in ("angry", "terrible", "unacceptable", "crash", "charged twice"))
        # One-line summary only (no control chars) — mirrors real model JSON hygiene.
        snippet = " ".join(user.split())[:120]
        out = {
            "category": cat,
            "priority": "urgent" if urgent else ("high" if neg else "medium"),
            "sentiment": "negative" if neg else "neutral",
            "summary": snippet,
            "suggested_reply": "Thanks for reaching out - we're looking into this right away.",
            "confidence": 0.8,
        }
        text = json.dumps(out)
        return ProviderResult(text, "mock-keyword-v1", len(user) // 4, len(text) // 4)

    async def ping(self) -> bool:
        return True

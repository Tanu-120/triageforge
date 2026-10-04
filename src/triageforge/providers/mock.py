import json
from typing import Any

from .base import ProviderResult

# category -> default queue
_QUEUE = {
    "billing": "billing_ops",
    "refund": "billing_ops",
    "bug": "engineering",
    "outage": "engineering",
    "feature_request": "success",
    "account": "general_support",
    "security": "trust_safety",
    "shipping": "logistics",
    "onboarding": "success",
    "cancellation": "retention",
    "compliance": "trust_safety",
    "other": "general_support",
}

_SLA = {"urgent": 2, "high": 8, "medium": 24, "low": 72}


class MockProvider:
    """Deterministic keyword model for tests, CI and offline demos."""

    name = "mock"

    async def generate_json(
        self, system: str, user: str, json_schema: dict[str, Any]
    ) -> ProviderResult:
        t = user.lower()
        cat = "other"
        for kw, c in [
            ("refund", "refund"),
            ("chargeback", "refund"),
            ("charged twice", "billing"),
            ("invoice", "billing"),
            ("charge", "billing"),
            ("outage", "outage"),
            ("down", "outage"),
            ("crash", "bug"),
            ("error", "bug"),
            ("hack", "security"),
            ("breach", "security"),
            ("unauthorized", "security"),
            ("ship", "shipping"),
            ("delivery", "shipping"),
            ("tracking", "shipping"),
            ("cancel", "cancellation"),
            ("unsubscribe", "cancellation"),
            ("onboard", "onboarding"),
            ("getting started", "onboarding"),
            ("gdpr", "compliance"),
            ("privacy", "compliance"),
            ("password", "account"),
            ("login", "account"),
            ("would be great", "feature_request"),
            ("feature", "feature_request"),
        ]:
            if kw in t:
                cat = c
                break

        urgent = any(w in t for w in ("asap", "urgent", "down", "outage", "breach", "hack"))
        neg = any(
            w in t
            for w in ("angry", "terrible", "unacceptable", "crash", "charged twice", "lawsuit")
        )
        priority = "urgent" if urgent else ("high" if neg else "medium")
        if neg:
            sentiment = "negative"
        elif "love" in t or "great" in t:
            sentiment = "positive"
        else:
            sentiment = "neutral"

        flags: list[str] = []
        if any(w in t for w in ("cancel", "unacceptable", "charged twice", "refund")):
            flags.append("churn")
        if any(w in t for w in ("fraud", "unauthorized", "stolen")):
            flags.append("fraud")
        if any(w in t for w in ("lawyer", "lawsuit", "gdpr", "legal")):
            flags.append("legal")
        if any(w in t for w in ("breach", "hack", "password", "card")):
            flags.append("data_exposure")
        if any(w in t for w in ("charge", "refund", "invoice", "charged")):
            flags.append("payment_dispute")
        if not flags:
            flags = ["none"]
        flags = flags[:4]

        severity = {"urgent": 9, "high": 7, "medium": 5, "low": 2}[priority]
        if "enterprise" in t:
            severity = min(10, severity + 1)

        kw_pool = ("refund", "crash", "login", "shipping", "outage", "security", "invoice")
        keywords = [w for w in kw_pool if w in t][:6]
        if not keywords:
            keywords = [cat.replace("_", " ")]

        escalate = priority in ("urgent", "high") and (
            cat in ("security", "outage", "refund") or "enterprise" in t or "churn" in flags
        )
        reason = (
            "High-severity signal with customer-risk indicators"
            if escalate
            else "Standard handling path — no escalation required"
        )

        actions = {
            "billing": [
                "Verify duplicate charges in ledger",
                "Issue provisional credit if confirmed",
            ],
            "refund": [
                "Confirm eligibility window",
                "Process refund and notify customer",
            ],
            "bug": ["Reproduce on latest build", "File engineering ticket with logs"],
            "outage": ["Check status page & on-call", "Send incident acknowledgement"],
            "security": ["Force session revoke", "Escalate to Trust & Safety"],
            "shipping": [
                "Pull carrier tracking",
                "Offer replacement if delayed > SLA",
            ],
            "cancellation": [
                "Offer retention save",
                "Process cancel if customer insists",
            ],
            "account": ["Verify identity", "Reset credentials securely"],
            "feature_request": [
                "Log in product board",
                "Send polite acknowledgement",
            ],
            "onboarding": [
                "Share quick-start checklist",
                "Schedule success check-in",
            ],
            "compliance": [
                "Open privacy request workflow",
                "Confirm legal hold status",
            ],
            "other": ["Clarify request", "Route to general support"],
        }.get(cat, ["Clarify request", "Route to general support"])

        snippet = " ".join(user.split())[:120]
        out = {
            "category": cat,
            "priority": priority,
            "sentiment": sentiment,
            "summary": snippet,
            "suggested_reply": (
                "Thanks for reaching out — I've classified your request "
                "and routed it to the right team. "
                "We'll update you within the stated SLA."
            ),
            "confidence": 0.86 if cat != "other" else 0.62,
            "assigned_queue": _QUEUE[cat],
            "sla_hours": _SLA[priority],
            "escalation_required": escalate,
            "escalation_reason": reason,
            "severity_score": severity,
            "risk_flags": flags,
            "keywords": keywords,
            "next_actions": actions[:3],
            "language": "en",
        }
        text = json.dumps(out)
        return ProviderResult(text, "mock-ops-v2", len(user) // 4, len(text) // 4)

    async def ping(self) -> bool:
        return True

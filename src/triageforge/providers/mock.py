import json
import re
from typing import Any

from ..routing import QUEUE_BY_CATEGORY, SEVERITY, SLA_HOURS
from .base import ProviderResult

_CAT_HINT = re.compile(r"\bcategory=([a-z_]+)\b")
_PRI_HINT = re.compile(r"\bpriority=(low|medium|high|urgent)\b")
_TONE_HINT = re.compile(r"\breply_tone=(empathetic|formal|brief)\b")


def _has_word(text: str, word: str) -> bool:
    return re.search(rf"\b{re.escape(word)}\b", text) is not None


_REPLIES = {
    "empathetic": (
        "I'm sorry you've had this experience — thank you for telling us. "
        "I've logged your request and routed it to the right team. "
        "We'll update you within the stated SLA."
    ),
    "formal": (
        "Thank you for contacting support. Your request has been classified "
        "and assigned to the appropriate queue. We will respond within the SLA window."
    ),
    "brief": ("Got it — ticket logged and routed. We'll update you within SLA."),
}


class MockProvider:
    """Deterministic keyword model for tests, CI and offline demos."""

    name = "mock"

    async def generate_json(
        self, system: str, user: str, json_schema: dict[str, Any]
    ) -> ProviderResult:
        t = user.lower()
        hint_cat = _CAT_HINT.search(t)
        hint_pri = _PRI_HINT.search(t)
        tone_m = _TONE_HINT.search(t)
        tone = tone_m.group(1) if tone_m else "empathetic"

        cat = hint_cat.group(1) if hint_cat and hint_cat.group(1) in QUEUE_BY_CATEGORY else "other"
        if cat == "other":
            for kw, c in [
                ("refund", "refund"),
                ("chargeback", "refund"),
                ("charged twice", "billing"),
                ("invoice", "billing"),
                ("charge", "billing"),
                ("outage", "outage"),
                ("crash", "bug"),
                ("error", "bug"),
                ("hack", "security"),
                ("breach", "security"),
                ("unauthorized", "security"),
                ("delivery", "shipping"),
                ("tracking", "shipping"),
                ("shipping", "shipping"),
                ("cancel", "cancellation"),
                ("onboard", "onboarding"),
                ("gdpr", "compliance"),
                ("password", "account"),
                ("login", "account"),
                ("would be great", "feature_request"),
                ("feature", "feature_request"),
            ]:
                if kw in t:
                    cat = c
                    break

        urgent = any(_has_word(t, w) for w in ("asap", "urgent", "outage", "breach", "hack"))
        if "not urgent" in t or "no rush" in t:
            urgent = False
        neg = any(
            phrase in t
            for phrase in ("angry", "terrible", "unacceptable", "crash", "charged twice", "lawsuit")
        )

        if hint_pri:
            priority = hint_pri.group(1)
        else:
            priority = "urgent" if urgent else ("high" if neg else "medium")

        if neg:
            sentiment = "negative"
        elif "love" in t or "great" in t or cat == "feature_request":
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

        severity = SEVERITY[priority]
        if "enterprise" in t:
            severity = min(10, severity + 1)

        kw_pool = ("refund", "crash", "login", "shipping", "outage", "security", "invoice", "csv")
        keywords = [w for w in kw_pool if w in t][:6] or [cat.replace("_", " ")]

        escalate = priority in ("urgent", "high") and (
            cat in ("security", "outage", "refund") or "enterprise" in t or "churn" in flags
        )
        reason = (
            "High-severity signal with customer-risk indicators"
            if escalate
            else "Standard handling path — no escalation required"
        )

        actions_map = {
            "billing": [
                "Verify duplicate charges in ledger",
                "Issue provisional credit if confirmed",
            ],
            "refund": ["Confirm eligibility window", "Process refund and notify customer"],
            "bug": ["Reproduce on latest build", "File engineering ticket with logs"],
            "outage": ["Check status page & on-call", "Send incident acknowledgement"],
            "security": ["Force session revoke", "Escalate to Trust & Safety"],
            "shipping": ["Pull carrier tracking", "Offer replacement if delayed > SLA"],
            "cancellation": ["Offer retention save", "Process cancel if customer insists"],
            "account": ["Verify identity", "Reset credentials securely"],
            "feature_request": ["Log in product board", "Send polite acknowledgement"],
            "onboarding": ["Share quick-start checklist", "Schedule success check-in"],
            "compliance": ["Open privacy request workflow", "Confirm legal hold status"],
            "other": ["Clarify request", "Route to general support"],
        }
        actions = actions_map.get(cat, actions_map["other"])

        body = user.split("\n", 1)[-1] if "\n" in user else user
        if body.startswith("(") and ")" in body[:80]:
            body = body.split(")", 1)[-1].strip()
        snippet = " ".join(body.split())[:120]

        rationale = (
            f"Matched signals for '{cat.replace('_', ' ')}' with priority '{priority}' "
            f"(sentiment={sentiment}, escalate={escalate})."
        )
        internal = (
            f"Route to {QUEUE_BY_CATEGORY[cat].replace('_', ' ')}. "
            f"SLA {SLA_HOURS[priority]}h. Flags: {', '.join(flags)}."
        )

        out = {
            "category": cat,
            "priority": priority,
            "sentiment": sentiment,
            "summary": snippet,
            "suggested_reply": _REPLIES.get(tone, _REPLIES["empathetic"]),
            "internal_note": internal,
            "rationale": rationale,
            "confidence": 0.9 if hint_cat or hint_pri else (0.86 if cat != "other" else 0.62),
            "assigned_queue": QUEUE_BY_CATEGORY[cat],
            "sla_hours": SLA_HOURS[priority],
            "escalation_required": escalate,
            "escalation_reason": reason,
            "severity_score": severity,
            "risk_flags": flags,
            "keywords": keywords,
            "next_actions": actions[:3],
            "language": "en",
        }
        # Suggest endpoint asks for a smaller schema — still fine (extra ignored upstream)
        text = json.dumps(out)
        return ProviderResult(text, "mock-ops-v3", len(user) // 4, len(text) // 4)

    async def ping(self) -> bool:
        return True

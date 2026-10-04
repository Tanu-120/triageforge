"""Deterministic queue / SLA / severity maps used by service + mock provider."""

QUEUE_BY_CATEGORY: dict[str, str] = {
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

SLA_HOURS: dict[str, int] = {"urgent": 2, "high": 8, "medium": 24, "low": 72}
SEVERITY: dict[str, int] = {"urgent": 9, "high": 7, "medium": 5, "low": 2}

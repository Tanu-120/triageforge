# API Contracts

Base URL `http://localhost:8000` · OpenAPI at `/docs` and `/openapi.json`.

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/v1/auth/register` | – | Create user (201 / 409) |
| POST | `/v1/auth/token` | – | Form login → JWT |
| GET | `/v1/taxonomy` | – | Public category/queue/risk map |
| POST | `/v1/triage` | JWT | **Deprecated** classic classification |
| POST | `/v2/triage` | JWT | Full ops triage pack |
| GET | `/v1/usage/me` | JWT | Rate-limit & token usage |
| GET | `/healthz` `/readyz` | – | Liveness / model readiness |

## Categories (12)
`billing`, `refund`, `bug`, `outage`, `feature_request`, `account`, `security`, `shipping`, `onboarding`, `cancellation`, `compliance`, `other`

## Queues
`billing_ops`, `engineering`, `trust_safety`, `logistics`, `success`, `retention`, `general_support`

## Request: `TriageRequest`
```json
{
  "category": "billing|refund|bug|… (optional analyst selection)",
  "priority": "low|medium|high|urgent (optional analyst selection)",
  "text": "string 10-4000 chars",
  "customer_tier": "free|pro|enterprise",
  "channel": "email|chat|phone|social",
  "product_area": "optional product name"
}
```
When `category` / `priority` are provided, they override model guesses (human-in-the-loop intake). Unknown fields are rejected (`422`).

## Response: `TriageV2` (ops pack)
```json
{
  "ticket_id": "tkt_ab12cd34ef",
  "category": "billing",
  "priority": "urgent",
  "summary": "…",
  "model": "qwen2.5:1.5b",
  "usage": {"prompt_tokens": 210, "completion_tokens": 88},
  "sentiment": "negative",
  "suggested_reply": "…",
  "confidence": 0.86,
  "pii_redacted": {"email": 1, "phone": 1},
  "latency_ms": 840,
  "assigned_queue": "billing_ops",
  "sla_hours": 2,
  "escalation_required": true,
  "escalation_reason": "High-severity signal with customer-risk indicators",
  "severity_score": 9,
  "risk_flags": ["churn", "payment_dispute"],
  "keywords": ["charge", "refund"],
  "next_actions": ["Verify duplicate charges in ledger", "Issue provisional credit if confirmed"],
  "language": "en",
  "channel": "email",
  "customer_tier": "pro",
  "product_area": "checkout"
}
```
`TriageV1` = first six fields only (frozen).

## Errors
| Code | Meaning |
|---|---|
| 401 | Missing/invalid/expired token or bad credentials |
| 409 | Username taken |
| 422 | Request failed Pydantic validation |
| 429 | Rate limit or daily token quota (`Retry-After`) |
| 502 | Model unreachable or output violated schema after retry |
| 503 | `/readyz`: model backend not reachable |

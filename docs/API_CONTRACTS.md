# API Contracts

Base URL `http://localhost:8000` · OpenAPI at `/docs` and `/openapi.json`.

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/v1/auth/register` | – | Create user (201 / 409) |
| POST | `/v1/auth/token` | – | Form login → JWT |
| POST | `/v1/triage` | JWT | **Deprecated** v1 classification |
| POST | `/v2/triage` | JWT | Full triage |
| GET | `/v1/usage/me` | JWT | Rate-limit & token usage |
| GET | `/healthz` `/readyz` | – | Liveness / model readiness |

## Request: `TriageRequest`
```json
{ "text": "string 10-4000 chars, must contain letters", "customer_tier": "free|pro|enterprise (optional)" }
```
Unknown fields are rejected (`422`).

## Response: `TriageV2`
```json
{
  "ticket_id": "tkt_ab12cd34ef",
  "category": "billing|bug|feature_request|account|other",
  "priority": "low|medium|high|urgent",
  "summary": "<=280 chars",
  "model": "qwen2.5:1.5b",
  "usage": {"prompt_tokens": 210, "completion_tokens": 88},
  "sentiment": "negative|neutral|positive",
  "suggested_reply": "<=1200 chars",
  "confidence": 0.0,
  "pii_redacted": {"email": 1, "phone": 1},
  "latency_ms": 840
}
```
`TriageV1` = first six fields only (frozen).

## Errors
| Code | Meaning |
|---|---|
| 401 | Missing/invalid/expired token or bad credentials (`WWW-Authenticate: Bearer`) |
| 409 | Username taken |
| 422 | Request failed Pydantic validation |
| 429 | Rate limit or daily token quota (`Retry-After` seconds) |
| 502 | Model unreachable or output violated schema after retry |
| 503 | `/readyz`: model backend not reachable |

## Versioning policy
Additive changes only within a version; breaking changes ship as `/v3`. Deprecated versions are marked in OpenAPI and removed after one release cycle.

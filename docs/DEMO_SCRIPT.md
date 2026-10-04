# 2-Minute Loom Script

**0:00–0:15 – Pitch.** "TriageForge turns raw support tickets into validated JSON using a local open model. JWT-protected, PII-safe, containerized."

**0:15–0:35 – Run it.** Terminal: `docker compose up --build` (pre-pulled). Show `/docs` and `curl localhost:8000/readyz` → `{"provider":"ollama"}`.

**0:35–0:55 – Auth.** Call `/v2/triage` with no token → **401**. Register, get token (show it's a JWT at jwt.io, note `exp`).

**0:55–1:25 – Core feature.** Send the ticket with an email + phone. Point at: category/priority, suggested_reply, `pii_redacted` counts, token usage, latency. Say "the model never saw the PII."

**1:25–1:45 – Guardrails.** Send `{"text":"hi"}` → **422**. Loop 11 requests → **429 + Retry-After**. Show `/v1/usage/me`.

**1:45–2:00 – Engineering.** Flash `ci.yml` green, `pytest` 8 passed, Dockerfile multi-stage, `ARCHITECTURE.md` diagram. Close with the Redis/Postgres next step.

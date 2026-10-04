# TriageForge 🔥

> JWT-secured support-ticket triage microservice powered by a **local open LLM** (Ollama · Qwen2.5) — with PII redaction, schema-enforced model output, per-user rate limits, token quotas and versioned API contracts.

Customer tickets go in; a validated JSON triage (category, priority, sentiment, summary, draft reply, confidence) comes out. PII is stripped **before** the model sees anything.

## Why it's production-minded
| Concern | Implementation |
|---|---|
| AuthN | OAuth2 password flow → short-lived JWT (HS256, `exp`/`jti`), bcrypt hashes |
| Contracts | Pydantic v2 on requests, responses **and model output** (`extra="forbid"`, enums, bounds) |
| LLM reliability | Ollama JSON-schema constrained decoding + validate + 1 repair retry → `502` on failure |
| Data safety | Regex PII redaction (email/phone/card) pre-inference; counts returned in `pii_redacted` |
| AI controls | Sliding-window rate limit + daily token quota per user (`429` + `Retry-After`) |
| Versioning | `/v1/triage` (frozen, deprecated) and `/v2/triage` (richer) from one service core |
| Portability | Provider interface: `ollama` (local) · `groq` (free tier) · `mock` (CI/offline) |
| Ops | `/healthz`, `/readyz` (probes model backend), multi-stage non-root Docker, GitHub Actions, pre-commit, strict mypy, ruff |

## Quick start (Docker + local open model)
```bash
cp .env.example .env            # set JWT_SECRET (>=32 chars)
docker compose up --build       # api :8000, ollama :11434, pulls qwen2.5:1.5b
```
Docs UI: http://localhost:8000/docs · Console: http://localhost:8000/

## Quick start (Docker, mock provider — no model download)
```bash
docker compose -f docker-compose.mock.yml up --build
```

## Quick start (dev, no Docker)
```bash
cp .env.example .env            # or use the committed-safe defaults via env vars
uv sync
# pick one inference backend:
#   PROVIDER=mock                         # offline / tests
#   PROVIDER=ollama && ollama pull qwen2.5:1.5b
#   PROVIDER=groq  && export GROQ_API_KEY=...
uv run uvicorn triageforge.main:app --reload
uv run pytest -q                # mock provider, no model needed
```

## Assignment checklist
| Deliverable | Where |
|---|---|
| Containerized FastAPI microservice | `Dockerfile`, `docker-compose.yml` |
| Open model local **or** free-tier API | Ollama (`qwen2.5:1.5b`) · Groq (`llama-3.1-8b-instant`) · Mock |
| JWT authentication | `/v1/auth/register`, `/v1/auth/token`, Bearer on triage |
| Pydantic v2 schema validation | request + response + **model output** contracts |
| Modular production repo | `src/triageforge/`, CI, pre-commit, docs |
| Architecture & API docs | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/API_CONTRACTS.md`](docs/API_CONTRACTS.md) |
| 2-min demo script (Loom) | [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) |

## Try it
```bash
curl -X POST localhost:8000/v1/auth/register -H 'content-type: application/json' \
  -d '{"username":"demo","password":"supersecret1"}'

TOKEN=$(curl -s -X POST localhost:8000/v1/auth/token \
  -d 'username=demo&password=supersecret1' | python -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

curl -X POST localhost:8000/v2/triage -H "authorization: Bearer $TOKEN" \
  -H 'content-type: application/json' \
  -d '{"text":"I was charged twice this month and nobody answers. Call me on +1 415 555 2671 ASAP","customer_tier":"pro"}'

curl localhost:8000/v1/usage/me -H "authorization: Bearer $TOKEN"
```

## Layout
```
src/triageforge/
  main.py         app factory + lifespan (shared httpx client, stores)
  config.py       pydantic-settings, fail-fast on missing secret
  security.py     bcrypt + JWT
  deps.py         DI: settings, provider, auth, rate-limit/quota guard
  controls.py     users, rate limiter, usage meter (in-memory)
  redaction.py    PII masking
  service.py      prompt -> model -> validate -> retry
  schemas.py      all Pydantic v2 contracts
  providers/      base Protocol, ollama, groq, mock
  routers/        auth, triage, health
tests/            auth, contracts, PII, versioning, rate limit, health
docs/             ARCHITECTURE.md, API_CONTRACTS.md, DEMO_SCRIPT.md
```

## Known limits / next steps
In-memory users & counters reset on restart and don't scale horizontally → Redis (limits) + Postgres (users). Add refresh tokens/key rotation, OpenTelemetry tracing, streaming, and a small eval set to track triage accuracy per model.

Docs: [Architecture](docs/ARCHITECTURE.md) · [API contracts](docs/API_CONTRACTS.md) · [Demo script](docs/DEMO_SCRIPT.md)

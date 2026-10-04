# TriageForge Ops

**JWT-secured support-operations microservice** built with FastAPI + Pydantic v2.  
It turns messy customer tickets into a validated **ops pack** — not just labels.

> Ticket in → PII redacted → open LLM → schema-checked JSON out  
> Category · Queue · SLA · Severity · Escalation · Risks · Next actions · Reply

Built for the Production-Grade AI Engineering Bootcamp (Week 2): containerized microservice, open model (local or free-tier), JWT auth, and strict schema validation.

---

## What you get

| Capability | Details |
|---|---|
| **Analyst console** | Sign-in UI, intake form, PII shield, result cards |
| **History sidebar** | Search, pin, reload any previous ops pack |
| **Dashboard** | KPIs, category/queue/priority charts, token usage |
| **Auto-suggest** | Fills category + priority from ticket text |
| **Reply tones** | Empathetic · Formal · Brief |
| **12 categories** | billing, refund, bug, outage, security, shipping, cancellation, … |
| **Queue routing** | billing_ops, engineering, trust_safety, logistics, … |
| **AI controls** | Per-minute rate limit + daily token quota (`429`) |
| **Versioned APIs** | `/v1/triage` (classic) · `/v2/triage` (full ops pack) |

---

## Models / providers

Swap backends with one env var (`PROVIDER`):

| Provider | Model | When to use |
|---|---|---|
| **`ollama`** | `qwen2.5:1.5b` (local open model) | Laptop / Docker demo with real local inference |
| **`groq`** | `llama-3.1-8b-instant` (free-tier API) | Cloud free-tier open model, no local GPU |
| **`mock`** | Deterministic keyword engine | CI, offline demos, fast UI walkthroughs |

All providers implement the same `LLMProvider` interface — handlers never import a vendor SDK.

---

## Quick start

### A) Dev mode (fastest — mock)
```bash
cp .env.example .env          # set JWT_SECRET (>= 32 chars)
# In .env: PROVIDER=mock
uv sync
uv run uvicorn triageforge.main:app --reload --host 127.0.0.1 --port 8000
```
- Console: http://127.0.0.1:8000/  
- OpenAPI: http://127.0.0.1:8000/docs  

### B) Docker + local Ollama model
```bash
cp .env.example .env          # PROVIDER=ollama, JWT_SECRET=...
docker compose up --build     # api :8000, ollama :11434, pulls qwen2.5:1.5b
```

### C) Docker mock (no model download)
```bash
docker compose -f docker-compose.mock.yml up --build
```

### D) Groq free tier
```bash
# .env
PROVIDER=groq
GROQ_API_KEY=your_key
GROQ_MODEL=llama-3.1-8b-instant
uv run uvicorn triageforge.main:app --reload
```

### Tests
```bash
uv run pytest -q
```

---

## Console walkthrough

1. **Create account / Sign in** (JWT + bcrypt)
2. Open **Triage workspace**
3. Paste a ticket (or click a sample)
4. Click **Auto-suggest** (optional) → category/priority filled
5. Set tier, channel, **reply tone**
6. Watch **PII shield** mask email/phone/card
7. **Generate ops pack** → queue, SLA due, severity, risks, actions, reply
8. Use **left sidebar** to reopen history (search / pin)
9. Open **Dashboard** for KPIs and charts
10. Mark feedback Helpful / Needs work · Download JSON report

### Demo ticket (billing + PII)
```text
I was charged twice this month and nobody answers. Email me at jane.doe@example.com or call +1 415 555 2671 ASAP, this is unacceptable.
```
Set: Category=`billing`, Priority=`urgent`, Tier=`pro`, Channel=`email`

---

## API surface (high level)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/v1/auth/register` | – | Create user |
| POST | `/v1/auth/token` | – | Login → JWT |
| POST | `/v2/suggest` | JWT | Auto-suggest category/priority |
| POST | `/v2/triage` | JWT | Full ops pack |
| POST | `/v1/triage` | JWT | Classic subset (deprecated) |
| GET | `/v1/history` | JWT | Sidebar history |
| GET | `/v1/history/{id}` | JWT | Reload one ticket |
| POST | `/v1/history/{id}/pin` | JWT | Pin / unpin |
| GET | `/v1/dashboard` | JWT | Dashboard KPIs |
| POST | `/v1/feedback` | JWT | Helpful / needs-work |
| GET | `/v1/taxonomy` | – | Public enum map |
| GET | `/healthz` `/readyz` | – | Liveness / model readiness |

Full contracts: [`docs/API_CONTRACTS.md`](docs/API_CONTRACTS.md)

---

## Architecture (request path)

```
Client (console / curl / Swagger)
   → JWT verify
   → Rate limit + token quota
   → Pydantic v2 request validation
   → PII redaction
   → LLMProvider (ollama | groq | mock)
   → Pydantic model-output validation (+ 1 repair retry)
   → Ops pack + history store + metering
```

Details: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

---

## Project layout

```
src/triageforge/
  main.py           FastAPI app + lifespan + console
  config.py         pydantic-settings
  security.py       bcrypt + JWT
  deps.py           DI (auth, provider, limits, history)
  controls.py       users, limiter, meter, feedback, history
  redaction.py      email / phone / card masking
  routing.py        category → queue / SLA / severity maps
  service.py        suggest + triage pipeline
  schemas.py        Pydantic v2 contracts
  providers/        ollama · groq · mock
  routers/          auth · triage · health · workspace
  static/           analyst console (dashboard + sidebar)
tests/              API, auth, PII, history, dashboard
docs/               architecture, API contracts, demo script
Dockerfile          multi-stage, non-root
docker-compose.yml  api + ollama + model pull
.github/workflows/  CI (ruff, mypy, pytest, docker build)
```

---

## Bootcamp deliverables checklist

| Deliverable | Status |
|---|---|
| Containerized FastAPI microservice | `Dockerfile`, `docker-compose.yml` |
| Open model local **or** free-tier API | Ollama `qwen2.5:1.5b` · Groq `llama-3.1-8b-instant` |
| JWT authentication | register / token / Bearer guards |
| Pydantic v2 schema validation | request + response + **model output** |
| Modular production repo + README | this repo |
| Architecture & API docs | `docs/` |
| Demo video script | [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) |

---

## Curl smoke test

```bash
curl -X POST localhost:8000/v1/auth/register -H 'content-type: application/json' \
  -d '{"username":"demo","password":"supersecret1"}'

TOKEN=$(curl -s -X POST localhost:8000/v1/auth/token \
  -d 'username=demo&password=supersecret1' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

curl -X POST localhost:8000/v2/triage -H "authorization: Bearer $TOKEN" \
  -H 'content-type: application/json' \
  -d '{"category":"billing","priority":"urgent","text":"Charged twice. Call +1 415 555 2671 ASAP","customer_tier":"pro","channel":"email","reply_tone":"empathetic"}'

curl localhost:8000/v1/dashboard -H "authorization: Bearer $TOKEN"
curl localhost:8000/v1/history -H "authorization: Bearer $TOKEN"
```

---

## Known limits / next steps

In-memory users, history, and counters reset on process restart and do not scale horizontally. Production path: Postgres (users/history), Redis (rate/quota), refresh tokens, HTTPS termination, OpenTelemetry, and a small eval set for triage accuracy per model.

---

## Docs

- [Architecture](docs/ARCHITECTURE.md)
- [API contracts](docs/API_CONTRACTS.md)
- [Loom / demo script](docs/DEMO_SCRIPT.md)

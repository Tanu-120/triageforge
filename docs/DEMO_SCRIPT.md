# TriageForge Ops — 3–4 Minute Loom Script

**Before recording**
- App running at http://127.0.0.1:8000/ (hard refresh)
- Tabs ready: Console, `/docs`, README / Dockerfile (optional)
- Sign out first so auth is visible

---

## Spoken script (follow with screen)

### 0:00–0:25 — Opening pitch
> “Hi — this is TriageForge Ops, my Week-2 production AI microservice.  
> It’s a JWT-secured FastAPI service that turns messy support tickets into a full operations pack: twelve categories, queue routing, SLA, severity, risk flags, next actions, and a customer reply.  
> PII is redacted before the model runs, and every model response is re-validated with Pydantic v2.”

**On screen:** landing / sign-in page. Point at model chip (`mock` / `ollama` / `groq`).

### 0:25–0:50 — Models we use
> “For inference I support three providers behind one interface.  
> **Ollama** runs a local open model — **Qwen 2.5 1.5B**.  
> **Groq** uses the free-tier open model **Llama 3.1 8B Instant**.  
> And **mock** is a deterministic keyword engine for CI and offline demos.  
> Today I’m demoing with mock so the walkthrough stays fast — same API contract as the real models.”

**On screen:** flash `.env.example` or README models table for 3–4 seconds.

### 0:50–1:10 — Auth (JWT)
> “First, authentication. I create an analyst account — username and password, with a show-password toggle.  
> Passwords are bcrypt-hashed, and login returns a short-lived JWT used as a Bearer token on every AI call.”

**Do:** Create account `demo_ops` / `bootcamp99` → land in console.

### 1:10–1:35 — Dashboard overview
> “After login you land on the **Dashboard**.  
> It shows tickets processed, escalations, average severity, helpful-rate from analyst feedback, plus charts by category, queue, and priority, and token usage against the daily quota.  
> This is what makes it feel like a real support-ops console, not a one-shot classifier.”

**Do:** Stay on Dashboard tab; point at KPI cards and bar charts (may be empty — say “fills after we triage”).

### 1:35–2:25 — Triage workspace + PII + ops pack
> “Switching to **Triage workspace**.  
> Flow is: paste ticket → optional auto-suggest → set category and priority → choose tone → generate.”

**Do:**
1. Click sample **Billing dispute** (or paste):
   ```
   I was charged twice this month and nobody answers. Email me at jane.doe@example.com or call +1 415 555 2671 ASAP, this is unacceptable.
   ```
2. Point at **PII shield** — email/phone masked as `[EMAIL]` / `[PHONE]`
3. Set tone **Empathetic** → **Generate ops pack**

> “Result is a full ops pack: billing category, billing-ops queue, SLA hours and due time, severity meter, escalation decision, risk flags, next actions for the agent, rationale, internal note, and a suggested customer reply.  
> I can copy the reply or download the JSON report.”

### 2:25–2:50 — Sidebar history (unique UX)
> “Every triage is saved in the **left sidebar history**.  
> I can search, pin important tickets, and click any item to reload the full previous result.  
> That makes demos and real analyst workflows much more practical.”

**Do:** Run one more sample (**Security alert** or **Feature ask**). Click first item in sidebar → show reload. Pin with ★.

### 2:50–3:15 — Dashboard after data + feedback
> “Back to **Dashboard** — KPIs and charts are now populated from history.  
> I’ll mark this triage Helpful — feedback feeds the helpful-rate metric.”

**Do:** Dashboard tab → point at updated bars → Workspace → Helpful.

### 3:15–3:40 — Production engineering
> “Under the hood: FastAPI dependency injection, versioned contracts `/v1` and `/v2`, rate limits and token quotas returning 429, multi-stage Docker, GitHub Actions CI with ruff, mypy, and pytest, plus architecture and API docs in the repo.”

**Do (quick cuts):** `/docs` → show secured endpoints · flash README / Dockerfile / `.github/workflows/ci.yml`.

### 3:40–4:00 — Close
> “So TriageForge Ops is a container-ready AI microservice: JWT auth, Pydantic v2 validation, PII-safe open-model inference with Ollama Qwen or Groq Llama, plus a real analyst console with history and dashboard. Thanks for watching.”

---

## Paste bank (ready to use)

**Billing + PII**
```text
I was charged twice this month and nobody answers. Email me at jane.doe@example.com or call +1 415 555 2671 ASAP, this is unacceptable.
```

**Security**
```text
I got an unauthorized login email. Please lock my account. Card on file 4242 4242 4242 4242 if you need to verify.
```

**Feature (low priority)**
```text
It would be great if you could export reports to CSV for our finance team. Not urgent, just a suggestion.
```

---

## Recording tips
- 1080p, mic close, slow mouse
- Hard refresh before start
- Prefer mock for smooth timing; say you’ll switch to Ollama/Groq for real inference
- If history is empty on dashboard at start, that’s fine — fill it mid-video

# 2-Minute Loom Script (Ops edition)

**0:00–0:15 – Pitch.**  
“TriageForge Ops is not a basic labeler. It’s a JWT-secured FastAPI microservice that turns tickets into an operations pack: 12 categories, queue routing, SLA, severity, risk flags, and next actions — with PII redacted before the open model runs.”

**0:15–0:35 – UI differentiators.**  
Open `/`. Show taxonomy chips + “Why this wins demos”. Open `/v1/taxonomy` in a tab.

**0:35–0:50 – Auth.**  
Create account / sign in. Click Show password. Mention JWT + bcrypt.

**0:50–1:20 – Core ops triage.**  
Paste billing dispute (email+phone). Show PII shield. Set tier=pro, channel=email. Run ops triage. Point to:
queue `billing_ops`, SLA hours, severity meter, escalation banner, risk flags, next actions, suggested reply.

**1:20–1:40 – Second scenario.**  
Security alert sample → `trust_safety` queue + escalation. Or shipping → `logistics`.

**1:40–1:50 – Guardrails.**  
Toggle `/v1 classic` vs `/v2 ops`. Mention 422/429. Flash `/docs`.

**1:50–2:00 – Engineering close.**  
Dockerfile, CI, ARCHITECTURE.md. “Same provider interface for mock, Ollama, or Groq.”

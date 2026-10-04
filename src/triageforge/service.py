import time
import uuid

from pydantic import ValidationError

from .providers import LLMProvider, ProviderError
from .redaction import redact
from .routing import QUEUE_BY_CATEGORY, SEVERITY, SLA_HOURS
from .schemas import Channel, LLMTriage, Queue, TriageRequest, TriageV2, Usage

SYSTEM = (
    "You are TriageForge, an enterprise support-operations engine. "
    "If the analyst already selected category/priority, respect those values. "
    "Assign an ops queue, set SLA hours, score severity (1-10), list risk flags, "
    "keywords, concrete next actions, and draft a short polite reply. "
    "Customer PII is masked as [EMAIL]/[PHONE]/[CARD]; never ask for it back. "
    "Respond ONLY with JSON matching the schema."
)


class TriageFailed(Exception):
    pass


async def triage_ticket(req: TriageRequest, provider: LLMProvider) -> TriageV2:
    start = time.perf_counter()
    clean, pii = redact(req.text)
    meta_parts: list[str] = []
    if req.category:
        meta_parts.append(f"category={req.category.value}")
    if req.priority:
        meta_parts.append(f"priority={req.priority.value}")
    if req.customer_tier:
        meta_parts.append(f"customer_tier={req.customer_tier}")
    if req.channel:
        meta_parts.append(f"channel={req.channel.value}")
    if req.product_area:
        meta_parts.append(f"product_area={req.product_area}")
    meta = f"({', '.join(meta_parts)})\n" if meta_parts else ""
    schema = LLMTriage.model_json_schema()
    prompt_tok = comp_tok = 0
    parsed: LLMTriage | None = None
    user = f"{meta}{clean}"
    res_model = "unknown"

    for _ in range(2):
        try:
            res = await provider.generate_json(SYSTEM, user, schema)
        except ProviderError as e:
            raise TriageFailed(str(e)) from e
        prompt_tok += res.prompt_tokens
        comp_tok += res.completion_tokens
        res_model = res.model
        try:
            parsed = LLMTriage.model_validate_json(res.text)
            break
        except ValidationError:
            user += "\n\nYour previous output violated the schema. Return valid JSON only."
    if parsed is None:
        raise TriageFailed("model output failed schema validation after retry")

    # Analyst selections win (human-in-the-loop intake)
    category = req.category or parsed.category
    priority = req.priority or parsed.priority
    queue_key = category.value
    assigned = (
        Queue(parsed.assigned_queue)
        if req.category is None
        else Queue(QUEUE_BY_CATEGORY.get(queue_key, "general_support"))
    )
    sla = SLA_HOURS.get(priority.value, parsed.sla_hours)
    severity = SEVERITY.get(priority.value, parsed.severity_score)

    flags = [f for f in parsed.risk_flags if f.value != "none"] or parsed.risk_flags

    return TriageV2(
        ticket_id=f"tkt_{uuid.uuid4().hex[:10]}",
        category=category,
        priority=priority,
        summary=parsed.summary,
        model=res_model,
        usage=Usage(prompt_tokens=prompt_tok, completion_tokens=comp_tok),
        sentiment=parsed.sentiment,
        suggested_reply=parsed.suggested_reply,
        confidence=parsed.confidence,
        pii_redacted=pii,
        latency_ms=int((time.perf_counter() - start) * 1000),
        assigned_queue=assigned,
        sla_hours=sla,
        escalation_required=parsed.escalation_required,
        escalation_reason=parsed.escalation_reason,
        severity_score=severity,
        risk_flags=flags,
        keywords=parsed.keywords,
        next_actions=parsed.next_actions,
        language=parsed.language,
        channel=req.channel or Channel.unknown,
        customer_tier=req.customer_tier,
        product_area=req.product_area,
    )

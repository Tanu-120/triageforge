import time
import uuid

from pydantic import ValidationError

from .providers import LLMProvider, ProviderError
from .redaction import redact
from .schemas import LLMTriage, TriageRequest, TriageV2, Usage

SYSTEM = (
    "You are a support-ticket triage engine. Classify the ticket and draft a short, polite reply. "
    "Customer PII is masked as [EMAIL]/[PHONE]/[CARD]; never ask for it back. "
    "Respond ONLY with JSON matching the schema."
)


class TriageFailed(Exception):
    pass


async def triage_ticket(req: TriageRequest, provider: LLMProvider) -> TriageV2:
    start = time.perf_counter()
    clean, pii = redact(req.text)
    tier = f"(customer tier: {req.customer_tier})\n" if req.customer_tier else ""
    schema = LLMTriage.model_json_schema()
    prompt_tok = comp_tok = 0
    parsed: LLMTriage | None = None
    user = f"{tier}{clean}"

    for _ in range(2):  # one repair retry on contract violation
        try:
            res = await provider.generate_json(SYSTEM, user, schema)
        except ProviderError as e:
            raise TriageFailed(str(e)) from e
        prompt_tok += res.prompt_tokens
        comp_tok += res.completion_tokens
        try:
            parsed = LLMTriage.model_validate_json(res.text)
            break
        except ValidationError:
            user += "\n\nYour previous output violated the schema. Return valid JSON only."
    if parsed is None:
        raise TriageFailed("model output failed schema validation after retry")

    return TriageV2(
        ticket_id=f"tkt_{uuid.uuid4().hex[:10]}",
        category=parsed.category,
        priority=parsed.priority,
        summary=parsed.summary,
        model=res.model,
        usage=Usage(prompt_tokens=prompt_tok, completion_tokens=comp_tok),
        sentiment=parsed.sentiment,
        suggested_reply=parsed.suggested_reply,
        confidence=parsed.confidence,
        pii_redacted=pii,
        latency_ms=int((time.perf_counter() - start) * 1000),
    )

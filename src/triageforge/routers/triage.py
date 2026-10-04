from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from ..deps import (
    FeedbackDep,
    LimiterDep,
    MeterDep,
    ProviderDep,
    SettingsDep,
    UserDep,
    current_user,
)
from ..schemas import (
    Category,
    Channel,
    FeedbackRequest,
    FeedbackResponse,
    Priority,
    Queue,
    ReplyTone,
    RiskFlag,
    Sentiment,
    SuggestRequest,
    SuggestResponse,
    TaxonomyResponse,
    TriageRequest,
    TriageV1,
    TriageV2,
    UsageReport,
)
from ..service import TriageFailed, suggest_ticket, triage_ticket

router = APIRouter(tags=["triage"])


@router.get("/v1/taxonomy", response_model=TaxonomyResponse)
def taxonomy() -> TaxonomyResponse:
    """Public map of enums — shows schema-driven design without auth."""
    return TaxonomyResponse(
        categories=[c.value for c in Category],
        priorities=[p.value for p in Priority],
        queues=[q.value for q in Queue],
        channels=[c.value for c in Channel],
        risk_flags=[r.value for r in RiskFlag],
        sentiments=[s.value for s in Sentiment],
        reply_tones=[t.value for t in ReplyTone],
    )


async def _run(req: TriageRequest, provider: ProviderDep, meter: MeterDep, user: str) -> TriageV2:
    try:
        result = await triage_ticket(req, provider)
    except TriageFailed as e:
        raise HTTPException(502, f"Upstream model failure: {e}") from e
    meter.add(user, result.usage.prompt_tokens + result.usage.completion_tokens)
    return result


@router.post("/v1/triage", response_model=TriageV1, deprecated=True)
async def triage_v1(
    req: TriageRequest, provider: ProviderDep, meter: MeterDep, user: UserDep
) -> TriageV1:
    """Frozen v1 contract: classification only."""
    full = await _run(req, provider, meter, user)
    return TriageV1.model_validate(full.model_dump(include=set(TriageV1.model_fields)))


@router.post("/v2/triage", response_model=TriageV2)
async def triage_v2(
    req: TriageRequest, provider: ProviderDep, meter: MeterDep, user: UserDep
) -> TriageV2:
    """v2 ops triage: queue, SLA due, severity, risks, notes, tone-aware reply."""
    return await _run(req, provider, meter, user)


@router.post("/v2/suggest", response_model=SuggestResponse)
async def suggest(
    req: SuggestRequest, provider: ProviderDep, meter: MeterDep, user: UserDep
) -> SuggestResponse:
    """Auto-suggest category + priority (fills the intake form)."""
    try:
        result = await suggest_ticket(req, provider)
    except TriageFailed as e:
        raise HTTPException(502, f"Upstream model failure: {e}") from e
    # Rough token accounting for suggest calls
    meter.add(user, 40)
    return result


@router.post("/v1/feedback", response_model=FeedbackResponse)
def feedback(
    body: FeedbackRequest,
    user: Annotated[str, Depends(current_user)],
    store: FeedbackDep,
) -> FeedbackResponse:
    """Analyst feedback on triage quality (does not consume rate limit)."""
    store.add(user, body.ticket_id, body.helpful, body.note)
    return FeedbackResponse(ticket_id=body.ticket_id, helpful=body.helpful)


@router.get("/v1/usage/me", response_model=UsageReport)
def my_usage(
    user: Annotated[str, Depends(current_user)],
    meter: MeterDep,
    limiter: LimiterDep,
    s: SettingsDep,
) -> UsageReport:
    """Auth-only — does not consume rate-limit budget."""
    return UsageReport(
        username=user,
        tokens_used_today=meter.used(user),
        daily_quota=s.daily_token_quota,
        requests_last_minute=limiter.current(user),
        rate_limit_per_min=s.rate_limit_per_min,
    )

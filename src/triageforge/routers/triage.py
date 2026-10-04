from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from ..deps import LimiterDep, MeterDep, ProviderDep, SettingsDep, UserDep, current_user
from ..schemas import TriageRequest, TriageV1, TriageV2, UsageReport
from ..service import TriageFailed, triage_ticket

router = APIRouter(tags=["triage"])


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
    """v2: adds sentiment, suggested reply, confidence, PII report, latency."""
    return await _run(req, provider, meter, user)


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

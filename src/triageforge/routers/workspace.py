"""History sidebar + analyst dashboard endpoints."""

from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException

from ..deps import FeedbackDep, HistoryDep, MeterDep, current_user
from ..schemas import DashboardStats, HistoryDetail, HistoryItem, TriageV2

router = APIRouter(tags=["workspace"])


def _to_item(raw: dict[str, object]) -> HistoryItem:
    result = raw["result"]
    assert isinstance(result, dict)
    return HistoryItem(
        ticket_id=str(raw["ticket_id"]),
        preview=str(raw["preview"]),
        pinned=bool(raw["pinned"]),
        created_at=str(raw["created_at"]),
        category=str(result.get("category", "other")),
        priority=str(result.get("priority", "medium")),
        severity_score=int(result.get("severity_score", 0) or 0),
        assigned_queue=str(result.get("assigned_queue", "general_support")),
    )


@router.get("/v1/history", response_model=list[HistoryItem])
def list_history(
    user: Annotated[str, Depends(current_user)], history: HistoryDep
) -> list[HistoryItem]:
    return [_to_item(i) for i in history.list(user)]


@router.get("/v1/history/{ticket_id}", response_model=HistoryDetail)
def get_history_item(
    ticket_id: str, user: Annotated[str, Depends(current_user)], history: HistoryDep
) -> HistoryDetail:
    item = history.get(user, ticket_id)
    if item is None:
        raise HTTPException(404, "History item not found")
    base = _to_item(item)
    result = item["result"]
    assert isinstance(result, dict)
    return HistoryDetail(**base.model_dump(), result=TriageV2.model_validate(result))


@router.post("/v1/history/{ticket_id}/pin", response_model=HistoryItem)
def pin_history(
    ticket_id: str, user: Annotated[str, Depends(current_user)], history: HistoryDep
) -> HistoryItem:
    item = history.toggle_pin(user, ticket_id)
    if item is None:
        raise HTTPException(404, "History item not found")
    return _to_item(item)


@router.delete("/v1/history/{ticket_id}")
def delete_history(
    ticket_id: str, user: Annotated[str, Depends(current_user)], history: HistoryDep
) -> dict[str, bool]:
    if not history.delete(user, ticket_id):
        raise HTTPException(404, "History item not found")
    return {"deleted": True}


@router.delete("/v1/history")
def clear_history(
    user: Annotated[str, Depends(current_user)], history: HistoryDep
) -> dict[str, int]:
    return {"cleared": history.clear(user)}


@router.get("/v1/dashboard", response_model=DashboardStats)
def dashboard(
    user: Annotated[str, Depends(current_user)],
    history: HistoryDep,
    feedback: FeedbackDep,
    meter: MeterDep,
) -> DashboardStats:
    raw = history.stats(user)
    return DashboardStats(
        total_tickets=cast(int, raw["total_tickets"]),
        escalations=cast(int, raw["escalations"]),
        avg_severity=cast(float, raw["avg_severity"]),
        pinned=cast(int, raw["pinned"]),
        feedback_count=feedback.count(user),
        helpful_rate=feedback.helpful_rate(user),
        tokens_used_today=meter.used(user),
        daily_quota=meter.daily_quota,
        by_category=cast(dict[str, int], raw["by_category"]),
        by_priority=cast(dict[str, int], raw["by_priority"]),
        by_queue=cast(dict[str, int], raw["by_queue"]),
    )

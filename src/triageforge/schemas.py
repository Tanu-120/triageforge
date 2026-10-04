from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Category(StrEnum):
    """Expanded support taxonomy — richer than a 4-bucket classifier."""

    billing = "billing"
    refund = "refund"
    bug = "bug"
    outage = "outage"
    feature_request = "feature_request"
    account = "account"
    security = "security"
    shipping = "shipping"
    onboarding = "onboarding"
    cancellation = "cancellation"
    compliance = "compliance"
    other = "other"


class Priority(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class Sentiment(StrEnum):
    negative = "negative"
    neutral = "neutral"
    positive = "positive"


class Queue(StrEnum):
    billing_ops = "billing_ops"
    engineering = "engineering"
    trust_safety = "trust_safety"
    logistics = "logistics"
    success = "success"
    retention = "retention"
    general_support = "general_support"


class Channel(StrEnum):
    email = "email"
    chat = "chat"
    phone = "phone"
    social = "social"
    unknown = "unknown"


class RiskFlag(StrEnum):
    churn = "churn"
    fraud = "fraud"
    legal = "legal"
    data_exposure = "data_exposure"
    payment_dispute = "payment_dispute"
    none = "none"


class ReplyTone(StrEnum):
    empathetic = "empathetic"
    formal = "formal"
    brief = "brief"


# ---------- auth ----------
class RegisterRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    username: str = Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=8, max_length=72)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# ---------- triage ----------
class TriageRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    category: Category | None = Field(default=None, description="Analyst-selected category")
    priority: Priority | None = Field(default=None, description="Analyst-selected priority")
    text: str = Field(min_length=10, max_length=4000, description="Raw customer ticket")
    customer_tier: str | None = Field(default=None, pattern=r"^(free|pro|enterprise)$")
    channel: Channel | None = Field(default=None, description="How the ticket arrived")
    product_area: str | None = Field(default=None, max_length=64, pattern=r"^[a-zA-Z0-9 _-]{2,64}$")
    reply_tone: ReplyTone = Field(
        default=ReplyTone.empathetic, description="Tone for customer reply"
    )

    @field_validator("text")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not any(c.isalpha() for c in v):
            raise ValueError("ticket must contain text")
        return v


class SuggestRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    text: str = Field(min_length=10, max_length=4000)

    @field_validator("text")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not any(c.isalpha() for c in v):
            raise ValueError("ticket must contain text")
        return v


class SuggestResponse(BaseModel):
    category: Category
    priority: Priority
    confidence: float = Field(ge=0, le=1)
    rationale: str
    pii_redacted: dict[str, int]


class FeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ticket_id: str = Field(min_length=8, max_length=40, pattern=r"^tkt_[a-f0-9]+$")
    helpful: bool
    note: str | None = Field(default=None, max_length=300)


class FeedbackResponse(BaseModel):
    ticket_id: str
    helpful: bool
    stored: bool = True


class LLMTriage(BaseModel):
    """Strict contract the *model* must satisfy. Anything else is rejected."""

    model_config = ConfigDict(extra="ignore")
    category: Category
    priority: Priority
    sentiment: Sentiment
    summary: str = Field(max_length=280)
    suggested_reply: str = Field(max_length=1200)
    internal_note: str = Field(max_length=500)
    rationale: str = Field(max_length=280)
    confidence: float = Field(ge=0, le=1)
    assigned_queue: Queue
    sla_hours: int = Field(ge=1, le=168)
    escalation_required: bool
    escalation_reason: str = Field(max_length=200)
    severity_score: int = Field(ge=1, le=10)
    risk_flags: list[RiskFlag] = Field(max_length=4)
    keywords: list[str] = Field(max_length=8)
    next_actions: list[str] = Field(min_length=1, max_length=5)
    language: str = Field(default="en", min_length=2, max_length=8)


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int


class TriageV1(BaseModel):
    ticket_id: str
    category: Category
    priority: Priority
    summary: str
    model: str
    usage: Usage


class TriageV2(TriageV1):
    sentiment: Sentiment
    suggested_reply: str
    confidence: float
    pii_redacted: dict[str, int]
    latency_ms: int
    assigned_queue: Queue
    sla_hours: int
    sla_due_at: datetime
    escalation_required: bool
    escalation_reason: str
    severity_score: int
    risk_flags: list[RiskFlag]
    keywords: list[str]
    next_actions: list[str]
    language: str
    channel: Channel
    customer_tier: str | None = None
    product_area: str | None = None
    reply_tone: ReplyTone = ReplyTone.empathetic
    rationale: str
    internal_note: str


class UsageReport(BaseModel):
    username: str
    tokens_used_today: int
    daily_quota: int
    requests_last_minute: int
    rate_limit_per_min: int


class TaxonomyResponse(BaseModel):
    """Public contract map — useful for UI + demos of schema-driven design."""

    categories: list[str]
    priorities: list[str]
    queues: list[str]
    channels: list[str]
    risk_flags: list[str]
    sentiments: list[str]
    reply_tones: list[str]


class HistoryItem(BaseModel):
    ticket_id: str
    preview: str
    pinned: bool
    created_at: str
    category: str
    priority: str
    severity_score: int
    assigned_queue: str


class HistoryDetail(HistoryItem):
    result: TriageV2


class DashboardStats(BaseModel):
    total_tickets: int
    escalations: int
    avg_severity: float
    pinned: int
    feedback_count: int
    helpful_rate: float | None
    tokens_used_today: int
    daily_quota: int
    by_category: dict[str, int]
    by_priority: dict[str, int]
    by_queue: dict[str, int]

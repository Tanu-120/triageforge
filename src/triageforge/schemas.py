from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Category(StrEnum):
    billing = "billing"
    bug = "bug"
    feature_request = "feature_request"
    account = "account"
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
    text: str = Field(min_length=10, max_length=4000, description="Raw customer ticket")
    customer_tier: str | None = Field(default=None, pattern=r"^(free|pro|enterprise)$")

    @field_validator("text")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not any(c.isalpha() for c in v):
            raise ValueError("ticket must contain text")
        return v


class LLMTriage(BaseModel):
    """Strict contract the *model* must satisfy. Anything else is rejected."""

    model_config = ConfigDict(extra="ignore")
    category: Category
    priority: Priority
    sentiment: Sentiment
    summary: str = Field(max_length=280)
    suggested_reply: str = Field(max_length=1200)
    confidence: float = Field(ge=0, le=1)


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


class UsageReport(BaseModel):
    username: str
    tokens_used_today: int
    daily_quota: int
    requests_last_minute: int
    rate_limit_per_min: int

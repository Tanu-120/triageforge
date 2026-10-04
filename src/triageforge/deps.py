from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer

from .config import Settings, get_settings
from .controls import FeedbackStore, RateLimiter, UsageMeter, UserStore
from .providers import LLMProvider
from .security import decode_token

oauth2 = OAuth2PasswordBearer(tokenUrl="/v1/auth/token")
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_provider(request: Request) -> LLMProvider:
    return request.app.state.provider  # type: ignore[no-any-return]


def get_users(request: Request) -> UserStore:
    return request.app.state.users  # type: ignore[no-any-return]


def get_limiter(request: Request) -> RateLimiter:
    return request.app.state.limiter  # type: ignore[no-any-return]


def get_meter(request: Request) -> UsageMeter:
    return request.app.state.meter  # type: ignore[no-any-return]


def get_feedback(request: Request) -> FeedbackStore:
    return request.app.state.feedback  # type: ignore[no-any-return]


ProviderDep = Annotated[LLMProvider, Depends(get_provider)]
UsersDep = Annotated[UserStore, Depends(get_users)]
LimiterDep = Annotated[RateLimiter, Depends(get_limiter)]
MeterDep = Annotated[UsageMeter, Depends(get_meter)]
FeedbackDep = Annotated[FeedbackStore, Depends(get_feedback)]


def current_user(token: Annotated[str, Depends(oauth2)], s: SettingsDep, users: UsersDep) -> str:
    err = HTTPException(401, "Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})
    try:
        sub = str(decode_token(token, s)["sub"])
    except jwt.PyJWTError:
        raise err from None
    if not users.exists(sub):
        raise err
    return sub


def guarded_user(
    user: Annotated[str, Depends(current_user)], limiter: LimiterDep, meter: MeterDep
) -> str:
    """Auth + AI-specific controls: per-minute rate limit and daily token quota."""
    if meter.over_quota(user):
        raise HTTPException(429, "Daily token quota exhausted", headers={"Retry-After": "3600"})
    wait = limiter.check(user)
    if wait is not None:
        raise HTTPException(429, "Rate limit exceeded", headers={"Retry-After": str(wait)})
    return user


UserDep = Annotated[str, Depends(guarded_user)]

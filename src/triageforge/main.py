from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse

from . import __version__
from .config import get_settings
from .controls import FeedbackStore, RateLimiter, UsageMeter, UserStore
from .providers import build_provider
from .routers import auth, health, triage


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    s = get_settings()
    async with httpx.AsyncClient(timeout=s.request_timeout_s) as client:
        app.state.provider = build_provider(s, client)
        app.state.users = UserStore()
        app.state.limiter = RateLimiter(s.rate_limit_per_min)
        app.state.meter = UsageMeter(s.daily_token_quota)
        app.state.feedback = FeedbackStore()
        yield


app = FastAPI(
    title="TriageForge",
    version=__version__,
    description="JWT-protected support-ticket triage over a local open LLM.",
    lifespan=lifespan,
)
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(triage.router)


def _console_index() -> Path:
    """Prefer package static; fall back to repo src/ during local edits."""
    packaged = Path(__file__).parent / "static" / "index.html"
    if packaged.is_file():
        return packaged
    return Path(__file__).resolve().parents[2] / "src" / "triageforge" / "static" / "index.html"


@app.get("/", include_in_schema=False)
def console() -> FileResponse:
    return FileResponse(
        _console_index(),
        media_type="text/html",
        headers={"Cache-Control": "no-store"},
    )

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse

from . import __version__
from .config import get_settings
from .controls import RateLimiter, UsageMeter, UserStore
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


_INDEX = Path(__file__).parent / "static" / "index.html"


@app.get("/", include_in_schema=False)
def console() -> FileResponse:
    return FileResponse(_INDEX, media_type="text/html")

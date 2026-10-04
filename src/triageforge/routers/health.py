from fastapi import APIRouter, HTTPException

from ..deps import ProviderDep

router = APIRouter(tags=["ops"])


@router.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(provider: ProviderDep) -> dict[str, str]:
    if not await provider.ping():
        raise HTTPException(503, f"provider '{provider.name}' not reachable")
    return {"status": "ready", "provider": provider.name}

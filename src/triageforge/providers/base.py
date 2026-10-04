from dataclasses import dataclass
from typing import Any, Protocol


class ProviderError(Exception):
    """Upstream model unavailable or misbehaving."""


@dataclass(frozen=True)
class ProviderResult:
    text: str
    model: str
    prompt_tokens: int
    completion_tokens: int


class LLMProvider(Protocol):
    name: str

    async def generate_json(
        self, system: str, user: str, json_schema: dict[str, Any]
    ) -> ProviderResult: ...

    async def ping(self) -> bool: ...

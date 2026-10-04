from typing import Any

import httpx

from .base import ProviderError, ProviderResult


class OllamaProvider:
    name = "ollama"

    def __init__(self, client: httpx.AsyncClient, base_url: str, model: str) -> None:
        self.client, self.base_url, self.model = client, base_url.rstrip("/"), model

    async def generate_json(
        self, system: str, user: str, json_schema: dict[str, Any]
    ) -> ProviderResult:
        body = {
            "model": self.model,
            "stream": False,
            "format": json_schema,  # Ollama structured outputs: constrains decoding to schema
            "options": {"temperature": 0.1},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        try:
            r = await self.client.post(f"{self.base_url}/api/chat", json=body)
            r.raise_for_status()
            d = r.json()
        except (httpx.HTTPError, ValueError) as e:
            raise ProviderError(f"ollama error: {e}") from e
        return ProviderResult(
            text=d["message"]["content"],
            model=self.model,
            prompt_tokens=d.get("prompt_eval_count", 0),
            completion_tokens=d.get("eval_count", 0),
        )

    async def ping(self) -> bool:
        try:
            return (await self.client.get(f"{self.base_url}/api/tags", timeout=3)).is_success
        except httpx.HTTPError:
            return False

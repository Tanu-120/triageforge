import json
from typing import Any

import httpx

from .base import ProviderError, ProviderResult


class GroqProvider:
    """Free-tier hosted open model (OpenAI-compatible endpoint)."""

    name = "groq"
    url = "https://api.groq.com/openai/v1"

    def __init__(self, client: httpx.AsyncClient, api_key: str, model: str) -> None:
        self.client, self.api_key, self.model = client, api_key, model

    async def generate_json(
        self, system: str, user: str, json_schema: dict[str, Any]
    ) -> ProviderResult:
        sys = f"{system}\nReturn JSON matching this schema: {json.dumps(json_schema)}"
        body = {
            "model": self.model,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": sys}, {"role": "user", "content": user}],
        }
        try:
            r = await self.client.post(
                f"{self.url}/chat/completions",
                json=body,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            r.raise_for_status()
            d = r.json()
        except (httpx.HTTPError, ValueError) as e:
            raise ProviderError(f"groq error: {e}") from e
        u = d.get("usage", {})
        return ProviderResult(
            d["choices"][0]["message"]["content"],
            self.model,
            u.get("prompt_tokens", 0),
            u.get("completion_tokens", 0),
        )

    async def ping(self) -> bool:
        return bool(self.api_key)

import httpx

from ..config import Settings
from .base import LLMProvider, ProviderError, ProviderResult
from .groq import GroqProvider
from .mock import MockProvider
from .ollama import OllamaProvider

__all__ = ["LLMProvider", "ProviderError", "ProviderResult", "build_provider"]


def build_provider(s: Settings, client: httpx.AsyncClient) -> LLMProvider:
    if s.provider == "ollama":
        return OllamaProvider(client, s.ollama_url, s.ollama_model)
    if s.provider == "groq":
        return GroqProvider(client, s.groq_api_key, s.groq_model)
    return MockProvider()

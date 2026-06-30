"""LLM local e gratuito via Ollama."""
from app.providers.base import LLMProvider


class OllamaLLM(LLMProvider):
    def generate(self, prompt: str) -> str:
        raise NotImplementedError("Implementar na Fase 1")

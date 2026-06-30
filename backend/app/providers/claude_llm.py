"""LLM via API da Anthropic (Claude). Plugar quando quiser modelo pago."""
from app.providers.base import LLMProvider


class ClaudeLLM(LLMProvider):
    def generate(self, prompt: str) -> str:
        raise NotImplementedError("Plugar depois")

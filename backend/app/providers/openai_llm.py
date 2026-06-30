"""LLM via API da OpenAI (GPT). Plugar quando quiser modelo pago."""
from app.providers.base import LLMProvider


class OpenAILLM(LLMProvider):
    def generate(self, prompt: str) -> str:
        raise NotImplementedError("Plugar depois")

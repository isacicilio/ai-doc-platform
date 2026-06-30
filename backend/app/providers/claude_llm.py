# app/providers/claude_llm.py
from anthropic import Anthropic

from app.config import settings
from app.providers.base import LLMProvider


class ClaudeLLM(LLMProvider):
    """
    Provider de LLM usando a API da Anthropic (Claude).

    Implementa a MESMA interface LLMProvider que o OpenAILLM. Pro resto do
    projeto, os dois são intercambiáveis — só muda o .env. Mas por dentro, o
    SDK da Anthropic tem diferenças importantes em relação ao da OpenAI.
    """

    def __init__(self) -> None:
        if not settings.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY não configurada. "
                "Defina no .env para usar o provider Claude."
            )
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model

    def generate(self, prompt: str, system: str | None = None) -> str:
        # Diferença 1: o system prompt NÃO vai dentro de messages.
        # Na Anthropic ele é um parâmetro próprio, separado.
        # Montamos os kwargs e só incluímos 'system' se ele existir.
        kwargs = {
            "model": self.model,
            "max_tokens": 1024,  # Diferença 2: max_tokens é OBRIGATÓRIO aqui
            "temperature": 0.2,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system

        response = self.client.messages.create(**kwargs)

        # Diferença 3: a resposta é uma lista de blocos de conteúdo.
        # Pegamos o texto do primeiro bloco.
        return response.content[0].text
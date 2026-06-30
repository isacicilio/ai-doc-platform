# app/providers/openai_llm.py
from openai import OpenAI

from app.config import settings
from app.providers.base import LLMProvider


class OpenAILLM(LLMProvider):
    """
    Provider de LLM usando a API da OpenAI.

    Implementa a interface LLMProvider. Toda a configuração (chave de API e
    modelo) vem do settings — ou seja, do .env. Nada fica hard-coded aqui.
    """

    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY não configurada. "
                "Defina no .env para usar o provider OpenAI."
            )
        # O client lê a chave do settings (que veio do .env)
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    def generate(self, prompt: str, system: str | None = None) -> str:
        # Monta a lista de mensagens no formato que a API espera.
        # O system prompt (se houver) vem primeiro, definindo o comportamento.
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,  # baixo = respostas mais factuais, menos "criativas"
        )

        # A resposta vem aninhada; extraímos só o texto da primeira escolha.
        return response.choices[0].message.content or ""
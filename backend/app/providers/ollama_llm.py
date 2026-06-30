# app/providers/ollama_llm.py
import httpx

from app.config import settings
from app.providers.base import LLMProvider


class OllamaLLM(LLMProvider):
    """
    Provider de LLM usando Ollama — modelos rodando LOCALMENTE na sua máquina.

    Implementa a mesma interface LLMProvider que os outros dois, mas é o mais
    diferente do trio:
    - Não tem chave de API (roda local, não é serviço de nuvem).
    - Não usa SDK próprio — falamos via HTTP puro com httpx.
    - É de graça: zero custo por requisição.

    Pré-requisito: ter o Ollama instalado e o modelo baixado
    (ex.: `ollama pull llama3.1`) e o servidor rodando.
    """

    def __init__(self) -> None:
        # Sem validação de chave: não existe chave. O que pode falhar é o
        # servidor não estar no ar — e isso a gente trata na hora da chamada,
        # não aqui, porque o servidor pode subir/cair a qualquer momento.
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model

    def generate(self, prompt: str, system: str | None = None) -> str:
        # A API do Ollama aceita 'system' como campo próprio no corpo do JSON.
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,  # False = resposta de uma vez (sem streaming)
            "options": {"temperature": 0.2},
        }
        if system:
            payload["system"] = system

        # timeout generoso: modelos locais podem ser lentos, dependendo da
        # máquina e do tamanho do modelo.
        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise RuntimeError(
                f"Falha ao chamar o Ollama em {self.base_url}. "
                f"O servidor está rodando? Detalhe: {e}"
            ) from e

        # A resposta JSON do Ollama traz o texto no campo 'response'.
        return response.json()["response"]
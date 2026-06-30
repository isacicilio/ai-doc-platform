"""Interfaces dos provedores. Permite trocar Ollama <-> Claude/OpenAI sem mexer na logica."""
from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Recebe textos e devolve seus vetores."""


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Recebe o prompt e devolve a resposta gerada."""

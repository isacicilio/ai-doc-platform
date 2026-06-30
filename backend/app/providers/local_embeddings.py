"""Embeddings locais e gratuitos via sentence-transformers."""
from app.providers.base import EmbeddingProvider

# TODO (Fase 1): carregar o modelo e implementar embed()
# from sentence_transformers import SentenceTransformer


class LocalEmbeddings(EmbeddingProvider):
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Implementar na Fase 1")

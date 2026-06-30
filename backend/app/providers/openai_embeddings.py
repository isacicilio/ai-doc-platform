# app/providers/openai_embeddings.py
from openai import OpenAI

from app.config import settings
from app.providers.base import EmbeddingProvider


class OpenAIEmbeddings(EmbeddingProvider):
    """
    Provider de embeddings usando a API da OpenAI.

    Implementa a interface EmbeddingProvider (a mesma do LocalEmbeddings).
    O modelo padrão é text-embedding-3-small, que produz vetores de dimensão
    1536 — que é o valor de embedding_dim na sua config atual.
    """

    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY não configurada. "
                "Defina no .env para usar embeddings da OpenAI."
            )
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.embedding_model_openai

    @property
    def dim(self) -> int:
        # Aqui a dimensão vem da config, não do modelo (a API não tem um
        # método pra "perguntar" a dimensão como o sentence-transformers tem).
        # Por isso a regra crítica importa: embedding_dim TEM que bater com o
        # modelo escolhido. text-embedding-3-small = 1536.
        return settings.embedding_dim

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        # A API aceita uma lista de textos de uma vez — uma única chamada
        # vetoriza todos os chunks do documento. Bem mais eficiente (e barato)
        # do que uma chamada por chunk.
        response = self.client.embeddings.create(
            model=self.model,
            input=texts,
        )
        # A resposta traz um item por texto de entrada, na mesma ordem.
        return [item.embedding for item in response.data]

    def embed_query(self, text: str) -> list[float]:
        # Um único texto: reaproveita o método de lote, como no local.
        return self.embed_documents([text])[0]
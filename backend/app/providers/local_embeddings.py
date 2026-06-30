# app/providers/local_embeddings.py
from app.config import settings
from app.providers.base import EmbeddingProvider


class LocalEmbeddings(EmbeddingProvider):
    """
    Provider de embeddings rodando LOCALMENTE, via sentence-transformers.

    Implementa a interface EmbeddingProvider (não a de LLM!). Gera vetores na
    sua máquina, de graça, sem chamar nuvem nenhuma. O modelo padrão é o
    all-MiniLM-L6-v2, que produz vetores de dimensão 384.

    ATENÇÃO À REGRA CRÍTICA: 384 precisa bater com settings.embedding_dim e com
    a coluna Vector no banco. Se usar este provider, ajuste embedding_dim=384.
    """

    def __init__(self) -> None:
        # Import adiado de propósito: sentence-transformers é uma dependência
        # pesada (puxa o PyTorch). Importar só aqui, dentro do __init__, evita
        # carregar tudo isso quando você está usando embeddings da OpenAI.
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(settings.embedding_model_local)

    @property
    def dim(self) -> int:
        # A dimensão real do modelo, perguntada diretamente a ele.
        # Para o all-MiniLM-L6-v2, isso retorna 384.
        return self.model.get_sentence_embedding_dimension()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        # Vetoriza vários textos de uma vez (usado na ingestão).
        # .tolist() converte os arrays do numpy em listas Python comuns,
        # que é o que o pgvector espera receber.
        vectors = self.model.encode(texts, convert_to_numpy=True)
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        # Vetoriza um único texto (usado na busca). Reaproveita o método de
        # lote passando uma lista de um item só e pegando o primeiro resultado.
        return self.embed_documents([text])[0]
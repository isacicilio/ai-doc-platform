# app/core/retrieval.py
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import Chunk
from app.providers.factory import get_embedding_provider


def retrieve_relevant_chunks(
    db: Session,
    question: str,
    top_k: int | None = None,
) -> list[Chunk]:
    """
    Busca os chunks mais relevantes para uma pergunta, por similaridade vetorial.

    Passos:
      1. Vetoriza a pergunta (embed_query) com o MESMO provider usado na
         ingestão — crucial: pergunta e chunks precisam viver no mesmo
         "espaço vetorial" pra comparação fazer sentido.
      2. Pede ao pgvector os top_k chunks mais próximos por distância de
         cosseno, direto no banco (rápido, sem trazer tudo pra memória).
    """
    if top_k is None:
        top_k = settings.top_k

    # 1) pergunta -> vetor (mesmo provider da ingestão, via factory)
    embedder = get_embedding_provider()
    query_vector = embedder.embed_query(question)

    # 2) busca vetorial: ordena pela distância de cosseno e pega os top_k.
    #    cosine_distance é um método do tipo Vector (pgvector). Quanto MENOR
    #    a distância, MAIOR a similaridade — por isso ordenamos ascendente.
    stmt = (
        select(Chunk)
        .order_by(Chunk.embedding.cosine_distance(query_vector))
        .limit(top_k)
    )

    return list(db.scalars(stmt).all())
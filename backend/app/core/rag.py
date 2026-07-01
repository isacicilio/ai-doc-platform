# app/core/rag.py
from sqlalchemy.orm import Session

from app.core.retrieval import retrieve_relevant_chunks
from app.providers.factory import get_llm_provider

# O system prompt define o COMPORTAMENTO do modelo. Aqui está a regra de ouro
# do RAG: responder SÓ com base no contexto, e admitir quando não sabe.
SYSTEM_PROMPT = (
    "Você é um assistente que responde perguntas sobre documentos. "
    "Use APENAS as informações do contexto fornecido para responder. "
    "Se a resposta não estiver no contexto, diga claramente que não "
    "encontrou essa informação no documento. Não invente. "
    "Responda em português, de forma clara e objetiva."
)


def _build_prompt(question: str, contexts: list[str]) -> str:
    """
    Monta o prompt final: junta os chunks recuperados como 'contexto' e
    anexa a pergunta. É o coração do 'Augmented' no RAG — enriquecemos a
    pergunta com a informação recuperada antes de mandar pro modelo.
    """
    contexto = "\n\n---\n\n".join(contexts)
    return (
        f"Contexto extraído do documento:\n\n{contexto}\n\n"
        f"========\n\n"
        f"Pergunta: {question}\n\n"
        f"Resposta (baseada apenas no contexto acima):"
    )


def answer_question(db: Session, question: str) -> dict:
    """
    Pipeline RAG completo:
      1. Recupera os chunks mais relevantes (Retrieval).
      2. Monta o prompt com esses chunks (Augmented).
      3. O LLM gera a resposta baseada no contexto (Generation).

    Retorna um dict com a resposta e os chunks usados como fonte — assim a
    API pode mostrar de ONDE veio a resposta (rastreabilidade).
    """
    # 1) Retrieval
    chunks = retrieve_relevant_chunks(db, question)

    # Caso não haja nada no banco (nenhum documento ingerido ainda).
    if not chunks:
        return {
            "answer": "Não há documentos no banco para responder à pergunta.",
            "sources": [],
        }

    # 2) Augmented: monta o prompt com o contexto recuperado
    contexts = [c.content for c in chunks]
    prompt = _build_prompt(question, contexts)

    # 3) Generation: o LLM (via factory) responde com base no contexto
    llm = get_llm_provider()
    answer = llm.generate(prompt, system=SYSTEM_PROMPT)

    # Devolve a resposta + as fontes (pra rastreabilidade)
    return {
        "answer": answer,
        "sources": [
            {
                "chunk_index": c.chunk_index,
                "document_id": c.document_id,
                "preview": c.content[:150],
            }
            for c in chunks
        ],
    }

# app/providers/base.py
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """
    Interface para qualquer provider de LLM (geração de texto).

    Todo provider concreto (OpenAI, Claude, Ollama) herda desta classe e
    implementa o método `generate`. O resto do projeto (RAG, API) só conhece
    esta interface — nunca a implementação concreta. Trocar de LLM vira mudar
    o .env, não o código.
    """

    @abstractmethod
    def generate(self, prompt: str, system: str | None = None) -> str:
        """
        Recebe um prompt (e um system prompt opcional) e devolve o texto gerado.

        - prompt: a mensagem do usuário (no RAG já vem com o contexto embutido).
        - system: instruções de comportamento do modelo (papel, tom, regras).
        - retorno: a resposta do modelo como string.
        """
        ...


class EmbeddingProvider(ABC):
    """
    Interface para qualquer provider de embeddings (texto -> vetor).

    Separada de LLMProvider de propósito: as duas responsabilidades são
    independentes. Dá pra gerar texto com Claude e embeddings com a OpenAI ao
    mesmo tempo — cada um se troca pelo .env sem afetar o outro.
    """

    @property
    @abstractmethod
    def dim(self) -> int:
        """
        Dimensão dos vetores que este provider produz.

        Existe pra validar contra settings.embedding_dim — aquela regra crítica:
        a dimensão TEM que bater com a coluna Vector no banco.
        text-embedding-3-small = 1536 | all-MiniLM-L6-v2 = 384.
        """
        ...

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Gera embeddings para vários textos de uma vez (usado na ingestão).

        Recebe N chunks e devolve N vetores, na mesma ordem. Em lote é bem mais
        eficiente do que vetorizar um por um.
        """
        ...

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """
        Gera o embedding de um único texto (usado na busca).

        Na hora da pergunta, vetorizamos a query do usuário pra comparar com os
        vetores dos chunks no banco. Devolve um único vetor.
        """
        ...
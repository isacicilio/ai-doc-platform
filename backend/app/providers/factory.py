# app/providers/factory.py
from functools import lru_cache

from app.config import settings
from app.providers.base import EmbeddingProvider, LLMProvider


@lru_cache
def get_llm_provider() -> LLMProvider:
    """
    Devolve o provider de LLM configurado no .env, já instanciado.

    Lê settings.llm_provider e decide qual classe criar. O resto do projeto
    chama esta função e recebe "um LLMProvider" — sem saber nem se importar
    se é OpenAI, Claude ou Ollama. É aqui, e só aqui, que essa escolha mora.

    Os imports são feitos DENTRO de cada ramo de propósito: assim só
    carregamos o SDK do provider que será realmente usado.
    """
    provider = settings.llm_provider.lower()

    if provider == "openai":
        from app.providers.openai_llm import OpenAILLM
        return OpenAILLM()

    if provider == "claude":
        from app.providers.claude_llm import ClaudeLLM
        return ClaudeLLM()

    if provider == "ollama":
        from app.providers.ollama_llm import OllamaLLM
        return OllamaLLM()

    raise ValueError(
        f"llm_provider inválido: '{settings.llm_provider}'. "
        "Use um de: openai, claude, ollama."
    )


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    """
    Devolve o provider de embeddings configurado no .env, já instanciado.

    Mesma lógica do get_llm_provider, mas para embeddings: lê
    settings.embedding_provider e devolve OpenAIEmbeddings ou LocalEmbeddings.
    """
    provider = settings.embedding_provider.lower()

    if provider == "openai":
        from app.providers.openai_embeddings import OpenAIEmbeddings
        return OpenAIEmbeddings()

    if provider == "local":
        from app.providers.local_embeddings import LocalEmbeddings
        return LocalEmbeddings()

    raise ValueError(
        f"embedding_provider inválido: '{settings.embedding_provider}'. "
        "Use um de: openai, local."
    )
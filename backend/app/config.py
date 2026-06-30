from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "AI Document Intelligence Platform"
    debug: bool = False

    # Banco de dados
    database_url: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/aidocs"
    )

    # Escolha de provider (trocável por .env, sem mexer no código)
    llm_provider: str = "openai"        # openai | claude | ollama
    embedding_provider: str = "openai"  # openai | local

    # Chaves de API
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None

    # Modelos
    claude_model: str = "claude-sonnet-4-6"
    openai_model: str = "gpt-4o-mini"
    ollama_model: str = "llama3.1"
    ollama_base_url: str = "http://localhost:11434"

    embedding_model_openai: str = "text-embedding-3-small"
    embedding_model_local: str = "all-MiniLM-L6-v2"

    # IMPORTANTE: tem que bater com o modelo de embedding escolhido
    # text-embedding-3-small = 1536 | all-MiniLM-L6-v2 = 384
    embedding_dim: int = 1536

    # Parâmetros do RAG
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 4


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
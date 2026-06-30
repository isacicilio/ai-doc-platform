"""Configuracao lida do .env."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    llm_provider: str = "ollama"
    embedding_provider: str = "local"
    ollama_model: str = "llama3.1"
    database_url: str = "postgresql://postgres:postgres@localhost:5432/docintel"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 4

    class Config:
        env_file = ".env"


settings = Settings()

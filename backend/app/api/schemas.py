# app/api/schemas.py
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AskRequest(BaseModel):
    """O que o cliente ENVIA para /ask."""
    question: str


class Source(BaseModel):
    """Uma fonte (chunk) que alimentou a resposta."""
    chunk_index: int
    document_id: int
    preview: str


class AskResponse(BaseModel):
    """O que /ask DEVOLVE: a resposta + as fontes."""
    answer: str
    sources: list[Source]


class DocumentOut(BaseModel):
    """Como um Document aparece nas respostas da API."""
    # from_attributes=True deixa o Pydantic ler direto de um objeto
    # SQLAlchemy (o Document do banco), sem conversão manual.
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    status: str
    created_at: datetime
# AI Document Intelligence Platform

Sistema RAG para fazer perguntas sobre documentos (PDF, DOCX...).
Stack local e gratuita: Ollama + sentence-transformers + PostgreSQL/pgvector + FastAPI.

## Arquitetura
Documento completo em [`docs/arquitetura-plano.md`](docs/arquitetura-plano.md).

## Status
Em construcao — Fase 0 (esqueleto do projeto).

## Como rodar (em breve)
1. Subir o banco:    `docker compose up -d`
2. Backend:          `cd backend && pip install -r requirements.txt`
3. Rodar a API:      `uvicorn app.main:app --reload`

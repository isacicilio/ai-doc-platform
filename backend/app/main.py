"""Entrypoint da API FastAPI."""
from fastapi import FastAPI

app = FastAPI(title="AI Document Intelligence Platform")


@app.get("/health")
def health():
    return {"status": "ok"}


# TODO (Fase 2): incluir os routers
# from app.api import documents, chat
# app.include_router(documents.router)
# app.include_router(chat.router)

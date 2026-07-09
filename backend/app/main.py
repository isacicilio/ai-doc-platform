# app/main.py
from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="AI Document Intelligence Platform",
    description="API de RAG — envie PDFs e faça perguntas sobre eles.",
    version="0.1.0",
)

# Registra todas as rotas definidas em app/api/routes.py
app.include_router(router)


@app.get("/")
def root():
    """Rota raiz: um 'oi' pra confirmar que a API está no ar."""
    return {"status": "ok", "message": "AI Document Intelligence Platform"}
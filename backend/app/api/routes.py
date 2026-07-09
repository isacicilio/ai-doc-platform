# app/api/routes.py
import os
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import AskRequest, AskResponse, DocumentOut
from app.core.rag import answer_question
from app.db.models import Document
from app.db.session import get_db
from app.services.ingestion import ingest_document

router = APIRouter()


@router.post("/documents", response_model=DocumentOut, status_code=201)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Recebe um PDF (upload), salva num arquivo temporário, dispara a
    ingestão (Bloco 4) e devolve o documento criado com seu status.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Envie um arquivo PDF (.pdf).")

    # A ingestão lê de um CAMINHO em disco, então salvamos o upload num
    # arquivo temporário. delete=False + close() antes: o Windows exige que
    # o arquivo esteja fechado pra outra função (o pypdf) poder abri-lo.
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    try:
        tmp.write(file.file.read())
        tmp.close()
        document = ingest_document(db, filename=file.filename, file_path=tmp.name)
    except ValueError as e:
        # Erros "esperados" da ingestão (ex.: PDF escaneado sem texto).
        raise HTTPException(status_code=422, detail=str(e))
    finally:
        # Não guardamos o PDF — só precisávamos do texto. Limpa o temporário.
        if os.path.exists(tmp.name):
            os.remove(tmp.name)

    return document


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest, db: Session = Depends(get_db)):
    """
    Recebe uma pergunta, roda o pipeline RAG (Bloco 5) e devolve a
    resposta + as fontes (os chunks usados).
    """
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="A pergunta não pode ser vazia.")
    return answer_question(db, payload.question)


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    """Lista os documentos enviados, do mais recente ao mais antigo."""
    stmt = select(Document).order_by(Document.created_at.desc())
    return list(db.scalars(stmt).all())


@router.get("/documents/{document_id}", response_model=DocumentOut)
def get_document(document_id: int, db: Session = Depends(get_db)):
    """Retorna um documento específico — útil pra checar o status dele."""
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
    return document
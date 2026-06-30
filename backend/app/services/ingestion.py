# app/services/ingestion.py
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.db.models import Chunk, Document
from app.providers.factory import get_embedding_provider
from app.services.chunking import chunk_text


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extrai todo o texto de um PDF, página por página, e junta num só texto.

    Usa o pypdf (que está no requirements.txt desde o Bloco 1). Cada página
    vira um trecho; juntamos com quebra de parágrafo pra preservar a noção de
    fronteira entre páginas (útil pro chunking depois).
    """
    reader = PdfReader(file_path)
    partes = []
    for pagina in reader.pages:
        texto = pagina.extract_text() or ""  # página sem texto vira string vazia
        if texto.strip():
            partes.append(texto.strip())
    return "\n\n".join(partes)


def ingest_document(db: Session, filename: str, file_path: str) -> Document:
    """
    Pipeline completo de ingestão de um PDF:
      1. Cria o registro Document (status 'processing').
      2. Extrai o texto do PDF.
      3. Quebra em chunks.
      4. Gera os embeddings de todos os chunks (em lote).
      5. Salva cada chunk + seu vetor no banco.
      6. Marca o Document como 'completed'.

    Recebe a sessão do banco de fora (injetada) — o serviço não cria nem fecha
    a sessão, quem controla isso é quem chama (a rota da API, no Bloco 6).
    """
    # 1) Cria o documento e já salva pra ter um ID.
    document = Document(filename=filename, status="processing")
    db.add(document)
    db.commit()
    db.refresh(document)  # recarrega pra pegar o id gerado pelo banco

    try:
        # 2) PDF -> texto
        texto = extract_text_from_pdf(file_path)
        if not texto.strip():
            raise ValueError("PDF sem texto extraível (pode ser um PDF escaneado).")

        # 3) texto -> chunks
        pedacos = chunk_text(texto)
        if not pedacos:
            raise ValueError("Nenhum chunk gerado a partir do texto.")

        # 4) chunks -> vetores (em lote, uma chamada só)
        embedder = get_embedding_provider()
        vetores = embedder.embed_documents(pedacos)

        # 5) salva cada chunk com seu vetor e a posição (chunk_index)
        for indice, (conteudo, vetor) in enumerate(zip(pedacos, vetores)):
            chunk = Chunk(
                document_id=document.id,
                content=conteudo,
                chunk_index=indice,
                embedding=vetor,
            )
            db.add(chunk)

        # 6) deu tudo certo: marca como completo e persiste
        document.status = "completed"
        db.commit()
        db.refresh(document)

    except Exception:
        # Se qualquer passo falhar, marca o documento como 'failed' e
        # re-lança o erro pra quem chamou tratar/registrar.
        document.status = "failed"
        db.commit()
        raise

    return document
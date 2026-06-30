# app/init_db.py
from sqlalchemy import text

from app.db.session import engine, Base
# importar os models registra as tabelas na metadata da Base
from app.db import models  # noqa: F401


def init_db() -> None:
    # 1) Liga a extensão pgvector no Postgres
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    print("Extensão pgvector habilitada.")

    # 2) Cria as tabelas (Document, Chunk)
    Base.metadata.create_all(bind=engine)
    print("Tabelas criadas com sucesso.")


if __name__ == "__main__":
    init_db()
    print("init_db concluído — Bloco 2 fechado.")
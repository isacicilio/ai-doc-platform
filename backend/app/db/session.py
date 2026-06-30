from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# echo=True mostra o SQL no terminal — ótimo pra aprender o que está rolando
engine = create_engine(settings.database_url, echo=settings.debug)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base que os models vão herdar
Base = declarative_base()


def get_db():
    """Dependency do FastAPI: abre uma sessão por request e fecha no fim."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
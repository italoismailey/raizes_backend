"""
session.py — Conexão com o banco de dados
Raízes do Nordeste — Projeto Back-End
Autor: Italo Ismailey G Durante | RU: 4471904 | UNINTER 2026

Decisão técnica: escolhi SQLite para o desenvolvimento local por não
exigir instalação de servidor. O parâmetro check_same_thread=False é
necessário no SQLite para permitir uso em múltiplas threads, que é o
comportamento padrão do FastAPI com requisições assíncronas.
Em produção, bastaria trocar a DATABASE_URL para PostgreSQL no .env.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

connect_args = (
    {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Dependency do FastAPI: abre uma sessão por requisição e
    garante o fechamento mesmo em caso de erro.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

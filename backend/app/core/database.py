from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings

settings = get_settings()


def normalizar_database_url(url: str) -> str:
    """Aponta URLs de Postgres para o driver psycopg (v3).

    O Neon (e o Render/Heroku) entregam a URL como "postgresql://..." ou
    "postgres://...", e o SQLAlchemy, sem driver explicito, tentaria o
    psycopg2, que nao esta instalado. Os parametros da URL (ex.:
    ?sslmode=require&channel_binding=require) sao mantidos e repassados ao
    libpq. Outras URLs (SQLite, ou ja com driver) passam sem mudanca.
    """
    for prefixo in ("postgresql://", "postgres://"):
        if url.startswith(prefixo):
            return "postgresql+psycopg://" + url[len(prefixo):]
    return url


def eh_sqlite(url: str) -> bool:
    return url.startswith("sqlite")


def _opcoes_engine(url: str) -> dict[str, Any]:
    if eh_sqlite(url):
        # O SQLite, por padrao, recusa uma conexao usada em thread diferente
        # da que a criou; o FastAPI roda as rotas sync num pool de threads.
        return {"connect_args": {"check_same_thread": False}}
    # pool_pre_ping: o Neon suspende o banco ocioso e derruba as conexoes
    # abertas; sem o ping, a primeira requisicao depois disso daria erro.
    return {"pool_pre_ping": True}


DATABASE_URL = normalizar_database_url(settings.database_url)

engine = create_engine(DATABASE_URL, **_opcoes_engine(DATABASE_URL))

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

import os
from pathlib import Path

TEST_DB_PATH = Path(__file__).parent / "test.db"

# Precisa rodar ANTES de qualquer import de app.*: app.core.database cria o
# engine (bind fixo nessa URL) assim que o modulo e importado pela primeira
# vez no processo. Definindo a env var aqui, o app inteiro nasce ja apontando
# para o banco de teste — os testes nunca tocam backend/cilindros.db.
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["SECRET_KEY"] = "chave-secreta-somente-para-os-testes"
os.environ["FRONTEND_ORIGIN"] = "http://localhost:5173"
os.environ["ENVIRONMENT"] = "local"

# create_all nao altera tabelas que ja existem: se sobrou um test.db de uma
# execucao interrompida (com schema antigo), ele e descartado antes de tudo.
TEST_DB_PATH.unlink(missing_ok=True)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.schemas.auth import UsuarioCriar  # noqa: E402
from app.services import auth_service  # noqa: E402
from auxiliares import mes_ano  # noqa: E402
from main import app  # noqa: E402

Base.metadata.create_all(bind=engine)

# Ordem que respeita as foreign keys: filhos antes dos pais.
TABELAS_PARA_LIMPAR = ["movimentacoes", "sessoes", "lotes", "tipos_cilindro", "usuarios"]


@pytest.fixture(autouse=True)
def banco_limpo():
    """Zera os dados (mantendo o schema) antes de cada teste, para nenhum
    teste depender de estado deixado por outro."""
    db = SessionLocal()
    try:
        for tabela in TABELAS_PARA_LIMPAR:
            db.execute(text(f"DELETE FROM {tabela}"))
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def usuaria_cadastrada():
    """Cria a usuaria direto pelo service (nao existe cadastro pela API) e
    devolve os dados usados, incluindo a senha em texto puro para o login."""
    dados = {"nome": "Usuaria Teste", "email": "usuaria@teste.com", "senha": "senha1234"}
    db = SessionLocal()
    try:
        auth_service.registrar_usuario(db, UsuarioCriar(**dados))
    finally:
        db.close()
    return dados


@pytest.fixture
def usuario_logado(client, usuaria_cadastrada):
    """Loga a usuaria cadastrada; devolve o client com o cookie de sessao
    ja setado, pronto para chamar rotas protegidas."""
    resposta = client.post(
        "/auth/login",
        json={"email": usuaria_cadastrada["email"], "senha": usuaria_cadastrada["senha"]},
    )
    assert resposta.status_code == 200
    return client


@pytest.fixture
def criar_tipo(usuario_logado):
    """Fabrica de tipos de cilindro: criar_tipo(nome=..., estoque_minimo=...)."""

    def _criar(nome="Cilindro 10L", estoque_minimo=2, **extras):
        resposta = usuario_logado.post(
            "/tipos", json={"nome": nome, "estoque_minimo": estoque_minimo, **extras}
        )
        assert resposta.status_code == 201, resposta.text
        return resposta.json()

    return _criar


@pytest.fixture
def tipo_criado(criar_tipo):
    return criar_tipo()


@pytest.fixture
def entrada(usuario_logado):
    """Registra uma entrada e devolve a movimentacao criada (com o lote)."""

    def _entrada(tipo_id, data_teste=None, quantidade=10, **extras):
        # Sem data_teste: teste feito no mes atual, ou seja, lote "ok" (vence
        # daqui a validade_anos).
        resposta = usuario_logado.post(
            "/movimentacoes/entrada",
            json={
                "tipo_id": tipo_id,
                "data_teste": data_teste or mes_ano(0),
                "quantidade": quantidade,
                **extras,
            },
        )
        assert resposta.status_code == 201, resposta.text
        return resposta.json()

    return _entrada


@pytest.fixture
def lote_com_estoque(usuario_logado, tipo_criado, entrada):
    """Lote com 10 cilindros testados no mes atual, como aparece em GET /lotes."""
    lote_id = entrada(tipo_criado["id"])["lote"]["id"]
    return next(lote for lote in usuario_logado.get("/lotes").json() if lote["id"] == lote_id)


def pytest_sessionfinish(session, exitstatus):
    # No Windows o arquivo nao pode ser apagado com conexoes ainda abertas
    # (diferente de Linux/macOS) — dispose() fecha todas as conexoes do pool
    # antes de remover o arquivo.
    engine.dispose()
    TEST_DB_PATH.unlink(missing_ok=True)

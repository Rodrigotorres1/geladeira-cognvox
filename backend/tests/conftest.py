import os
from pathlib import Path

TEST_DB_PATH = Path(__file__).parent / "test.db"

# Precisa rodar ANTES de qualquer import de app.*: app.core.database cria o
# engine (bind fixo nessa URL) assim que o modulo e importado pela primeira
# vez no processo. Definindo a env var aqui, o app inteiro nasce ja apontando
# para o banco de teste — os testes nunca tocam backend/geladeira.db.
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["SECRET_KEY"] = "chave-secreta-somente-para-os-testes"
os.environ["FRONTEND_ORIGIN"] = "http://localhost:5173"
os.environ["ENVIRONMENT"] = "local"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from main import app  # noqa: E402

Base.metadata.create_all(bind=engine)

# Ordem que respeita as foreign keys: filhos antes dos pais.
TABELAS_PARA_LIMPAR = ["movimentacoes", "sessoes", "itens_estoque", "usuarios"]


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
def usuario_logado(client):
    """Registra e loga um usuario; devolve o client com o cookie de sessao
    ja setado, pronto para chamar rotas protegidas."""
    dados = {"nome": "Usuaria Teste", "email": "usuaria@teste.com", "senha": "senha1234"}
    client.post("/auth/registro", json=dados)
    resposta = client.post(
        "/auth/login", json={"email": dados["email"], "senha": dados["senha"]}
    )
    assert resposta.status_code == 200
    return client


@pytest.fixture
def item_criado(usuario_logado):
    """Cria um item de estoque com o usuario_logado e devolve o item criado."""
    resposta = usuario_logado.post(
        "/itens",
        json={"nome": "Item de teste", "quantidade": 10, "unidade": "un", "valor_unitario": 5.0},
    )
    assert resposta.status_code == 201
    return resposta.json()


def pytest_sessionfinish(session, exitstatus):
    # No Windows o arquivo nao pode ser apagado com conexoes ainda abertas
    # (diferente de Linux/macOS) — dispose() fecha todas as conexoes do pool
    # antes de remover o arquivo.
    engine.dispose()
    TEST_DB_PATH.unlink(missing_ok=True)

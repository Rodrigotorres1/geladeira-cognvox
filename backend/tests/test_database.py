import pytest

from app.core.config import get_settings
from app.core.database import _opcoes_engine, normalizar_database_url


@pytest.mark.parametrize(
    "url, esperado",
    [
        # Formato do Neon: parametros de SSL mantidos na URL
        (
            "postgresql://usuario:senha@ep-xyz.sa-east-1.aws.neon.tech/cilindros?sslmode=require",
            "postgresql+psycopg://usuario:senha@ep-xyz.sa-east-1.aws.neon.tech/cilindros?sslmode=require",
        ),
        (
            "postgresql://u:s@host/db?sslmode=require&channel_binding=require",
            "postgresql+psycopg://u:s@host/db?sslmode=require&channel_binding=require",
        ),
        # Formato antigo (Heroku/Render)
        ("postgres://u:s@host:5432/db", "postgresql+psycopg://u:s@host:5432/db"),
        # Ja com driver explicito ou SQLite: sem mudanca
        ("postgresql+psycopg://u:s@host/db", "postgresql+psycopg://u:s@host/db"),
        ("sqlite:///./cilindros.db", "sqlite:///./cilindros.db"),
    ],
)
def test_normaliza_database_url(url, esperado):
    assert normalizar_database_url(url) == esperado


def test_check_same_thread_so_no_sqlite():
    assert _opcoes_engine("sqlite:///./cilindros.db") == {
        "connect_args": {"check_same_thread": False}
    }
    opcoes_postgres = _opcoes_engine("postgresql+psycopg://u:s@host/db?sslmode=require")
    assert "connect_args" not in opcoes_postgres
    assert opcoes_postgres["pool_pre_ping"] is True


# --- Cookie de sessao (mesmo site via proxy /api) ---


def _cookie_de_sessao(resposta):
    return next(
        cabecalho
        for cabecalho in resposta.headers.get_list("set-cookie")
        if cabecalho.startswith("session_id=")
    )


def _login(client, usuaria):
    return client.post("/auth/login", json={"email": usuaria["email"], "senha": usuaria["senha"]})


def test_cookie_local_e_lax_sem_secure(client, usuaria_cadastrada):
    cookie = _cookie_de_sessao(_login(client, usuaria_cadastrada)).lower()

    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert "secure" not in cookie


def test_cookie_em_producao_e_lax_com_secure(client, usuaria_cadastrada, monkeypatch):
    monkeypatch.setattr(get_settings(), "environment", "production")

    cookie = _cookie_de_sessao(_login(client, usuaria_cadastrada)).lower()

    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert "secure" in cookie
    assert "samesite=none" not in cookie

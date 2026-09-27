import uuid
from datetime import timedelta

from app.core.database import SessionLocal
from app.core.tempo import agora_utc
from app.models.sessao import Sessao


def test_cadastro_publico_nao_existe(client):
    resposta = client.post(
        "/auth/registro",
        json={"nome": "Rodrigo", "email": "rodrigo@teste.com", "senha": "senha1234"},
    )

    assert resposta.status_code in (404, 405)


def test_login_com_credenciais_corretas(client, usuaria_cadastrada):
    resposta = client.post(
        "/auth/login",
        json={"email": usuaria_cadastrada["email"], "senha": usuaria_cadastrada["senha"]},
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["email"] == usuaria_cadastrada["email"]
    assert "senha" not in corpo
    assert "senha_hash" not in corpo
    assert "session_id" in resposta.cookies


def test_login_com_senha_incorreta_falha(client, usuaria_cadastrada):
    resposta = client.post(
        "/auth/login", json={"email": usuaria_cadastrada["email"], "senha": "senha-errada"}
    )

    assert resposta.status_code == 401
    assert resposta.json()["detail"] == "E-mail ou senha inválidos"
    assert "session_id" not in resposta.cookies


def test_login_com_senha_maior_que_72_caracteres_retorna_422_e_nao_500(
    client, usuaria_cadastrada
):
    resposta = client.post(
        "/auth/login", json={"email": usuaria_cadastrada["email"], "senha": "a" * 100}
    )

    assert resposta.status_code == 422


def test_me_retorna_a_usuaria_logada(usuario_logado, usuaria_cadastrada):
    resposta = usuario_logado.get("/auth/me")

    assert resposta.status_code == 200
    assert resposta.json()["email"] == usuaria_cadastrada["email"]


def test_rota_protegida_sem_sessao_responde_nao_autenticado(client):
    resposta = client.get("/auth/me")

    assert resposta.status_code == 401
    assert resposta.json()["detail"] == "Não autenticado"


def test_logout_encerra_a_sessao_no_servidor(usuario_logado):
    cookie_antigo = usuario_logado.cookies.get("session_id")

    resposta = usuario_logado.post("/auth/logout")

    assert resposta.status_code == 204
    assert usuario_logado.get("/auth/me").status_code == 401
    # Reenviar o cookie antigo nao adianta: a sessao foi apagada do banco.
    usuario_logado.cookies.set("session_id", cookie_antigo)
    assert usuario_logado.get("/auth/me").status_code == 401


def test_sessao_expirada_nao_autentica(usuario_logado):
    db = SessionLocal()
    try:
        for sessao in db.query(Sessao).all():
            sessao.expira_em = agora_utc() - timedelta(minutes=1)
        db.commit()
    finally:
        db.close()

    resposta = usuario_logado.get("/auth/me")

    assert resposta.status_code == 401
    assert resposta.json()["detail"] == "Não autenticado"


def test_cookie_adulterado_nao_autentica(client, usuaria_cadastrada):
    client.cookies.set("session_id", "valor-forjado")

    assert client.get("/auth/me").status_code == 401


def test_id_da_usuaria_e_uuid_v4(usuario_logado):
    assert uuid.UUID(usuario_logado.get("/auth/me").json()["id"]).version == 4

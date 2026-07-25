def test_registro_com_sucesso(client):
    resposta = client.post(
        "/auth/registro",
        json={"nome": "Rodrigo", "email": "rodrigo@teste.com", "senha": "senha1234"},
    )

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["nome"] == "Rodrigo"
    assert corpo["email"] == "rodrigo@teste.com"
    assert "id" in corpo
    assert "senha" not in corpo
    assert "senha_hash" not in corpo


def test_registro_com_email_duplicado_falha(client):
    dados = {"nome": "Rodrigo", "email": "duplicado@teste.com", "senha": "senha1234"}

    primeiro_registro = client.post("/auth/registro", json=dados)
    assert primeiro_registro.status_code == 201

    segundo_registro = client.post("/auth/registro", json=dados)
    assert segundo_registro.status_code == 409


def test_registro_com_senha_maior_que_72_caracteres_retorna_422_e_nao_500(client):
    senha_muito_longa = "a" * 100

    resposta = client.post(
        "/auth/registro",
        json={"nome": "Rodrigo", "email": "senha-longa@teste.com", "senha": senha_muito_longa},
    )

    assert resposta.status_code == 422


def test_login_com_credenciais_corretas(client):
    client.post(
        "/auth/registro",
        json={"nome": "Rodrigo", "email": "login-ok@teste.com", "senha": "senha1234"},
    )

    resposta = client.post(
        "/auth/login", json={"email": "login-ok@teste.com", "senha": "senha1234"}
    )

    assert resposta.status_code == 200
    assert resposta.json()["email"] == "login-ok@teste.com"
    assert "session_id" in resposta.cookies


def test_login_com_senha_incorreta_falha(client):
    client.post(
        "/auth/registro",
        json={"nome": "Rodrigo", "email": "login-errado@teste.com", "senha": "senha1234"},
    )

    resposta = client.post(
        "/auth/login", json={"email": "login-errado@teste.com", "senha": "senha-errada"}
    )

    assert resposta.status_code == 401
    assert "session_id" not in resposta.cookies

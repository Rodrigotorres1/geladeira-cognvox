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

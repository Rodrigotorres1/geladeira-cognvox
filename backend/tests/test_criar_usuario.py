import pytest

import criar_usuario
from app.core.database import SessionLocal
from app.models.usuario import Usuario


@pytest.fixture
def senhas_digitadas(monkeypatch):
    """Simula o que a pessoa digita nos prompts de senha do getpass."""

    def _digitar(*senhas):
        respostas = iter(senhas)
        monkeypatch.setattr(criar_usuario.getpass, "getpass", lambda prompt="": next(respostas))

    return _digitar


def _total_usuarios():
    db = SessionLocal()
    try:
        return db.query(Usuario).count()
    finally:
        db.close()


def _login(client, email, senha):
    return client.post("/auth/login", json={"email": email, "senha": senha})


def test_cria_a_usuaria_com_banco_vazio_e_o_login_funciona(client, senhas_digitadas):
    senhas_digitadas("senha1234", "senha1234")

    codigo = criar_usuario.main(["--nome", "Maria", "--email", "maria@teste.com"])

    assert codigo == 0
    assert _total_usuarios() == 1
    assert _login(client, "maria@teste.com", "senha1234").status_code == 200


def test_recusa_criar_se_ja_existe_qualquer_usuario(usuaria_cadastrada, senhas_digitadas, capsys):
    senhas_digitadas("senha1234", "senha1234")

    codigo = criar_usuario.main(["--nome", "Outra", "--email", "outra@teste.com"])

    assert codigo == 1
    assert _total_usuarios() == 1
    assert "--redefinir-senha" in capsys.readouterr().err


def test_recusa_criar_com_mesmo_email_da_usuaria_existente(usuaria_cadastrada, senhas_digitadas):
    senhas_digitadas("senha1234", "senha1234")

    codigo = criar_usuario.main(["--nome", "Maria", "--email", usuaria_cadastrada["email"]])

    assert codigo == 1
    assert _total_usuarios() == 1


def test_redefinir_senha_troca_a_senha_da_usuaria(client, usuaria_cadastrada, senhas_digitadas):
    senhas_digitadas("nova-senha-123", "nova-senha-123")

    codigo = criar_usuario.main(["--redefinir-senha", "--email", usuaria_cadastrada["email"]])

    assert codigo == 0
    assert _login(client, usuaria_cadastrada["email"], "nova-senha-123").status_code == 200
    assert _login(client, usuaria_cadastrada["email"], usuaria_cadastrada["senha"]).status_code == 401


def test_redefinir_senha_de_email_inexistente_falha(usuaria_cadastrada, senhas_digitadas):
    senhas_digitadas("nova-senha-123", "nova-senha-123")

    codigo = criar_usuario.main(["--redefinir-senha", "--email", "ninguem@teste.com"])

    assert codigo == 1


def test_senhas_diferentes_nao_criam_usuaria(senhas_digitadas):
    senhas_digitadas("senha1234", "senha-diferente")

    codigo = criar_usuario.main(["--nome", "Maria", "--email", "maria@teste.com"])

    assert codigo == 1
    assert _total_usuarios() == 0


def test_senha_curta_nao_cria_usuaria(senhas_digitadas):
    senhas_digitadas("curta", "curta")

    codigo = criar_usuario.main(["--nome", "Maria", "--email", "maria@teste.com"])

    assert codigo == 1
    assert _total_usuarios() == 0


def test_criar_sem_nome_e_erro_de_uso():
    with pytest.raises(SystemExit) as erro:
        criar_usuario.main(["--email", "maria@teste.com"])

    assert erro.value.code == 2

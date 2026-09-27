import pytest

from app.core.validacao import traduzir_erro


def _primeiro_erro(resposta):
    assert resposta.status_code == 422
    return resposta.json()["detail"][0]


# --- Traducao das mensagens pela API ---


def test_campo_obrigatorio(usuario_logado):
    erro = _primeiro_erro(usuario_logado.post("/tipos", json={"estoque_minimo": 1}))

    assert erro["loc"] == ["body", "nome"]
    assert erro["msg"] == "Nome: campo obrigatório."


def test_maior_que(usuario_logado, lote_com_estoque):
    erro = _primeiro_erro(
        usuario_logado.post(
            "/movimentacoes/saida", json={"lote_id": lote_com_estoque["id"], "quantidade": 0}
        )
    )

    assert erro["msg"] == "Quantidade: deve ser maior que 0."


def test_maior_ou_igual(usuario_logado):
    erro = _primeiro_erro(
        usuario_logado.post("/tipos", json={"nome": "Cilindro", "estoque_minimo": -1})
    )

    assert erro["msg"] == "Estoque mínimo: deve ser maior ou igual a 0."


@pytest.mark.parametrize("valor", [1.5, "abc"])
def test_numero_inteiro_invalido(usuario_logado, valor):
    erro = _primeiro_erro(
        usuario_logado.post("/tipos", json={"nome": "Cilindro", "estoque_minimo": valor})
    )

    assert erro["msg"] == "Estoque mínimo: informe um número inteiro."


def test_texto_invalido(usuario_logado):
    erro = _primeiro_erro(usuario_logado.post("/tipos", json={"nome": 123, "estoque_minimo": 1}))

    assert erro["msg"] == "Nome: informe um texto."


def test_texto_longo_demais(client):
    erro = _primeiro_erro(
        client.post("/auth/login", json={"email": "maria@exemplo.com", "senha": "a" * 100})
    )

    assert erro["msg"] == "Senha: deve ter no máximo 72 caracteres."


def test_outros_erros_tem_mensagem_generica_em_portugues(usuario_logado):
    erro = _primeiro_erro(
        usuario_logado.post(
            "/movimentacoes/entrada",
            json={"tipo_id": "nao-e-um-uuid", "data_teste": "04/2020", "quantidade": 1},
        )
    )

    assert erro["msg"] == "Tipo de cilindro: valor inválido."


def test_email_invalido_usa_a_mensagem_generica(client):
    erro = _primeiro_erro(client.post("/auth/login", json={"email": "sem-arroba", "senha": "x"}))

    assert erro["msg"] == "E-mail: valor inválido."


def test_mensagem_da_data_do_teste_nao_e_alterada(usuario_logado, tipo_criado):
    erro = _primeiro_erro(
        usuario_logado.post(
            "/movimentacoes/entrada",
            json={"tipo_id": tipo_criado["id"], "data_teste": "13/2020", "quantidade": 1},
        )
    )

    assert erro["msg"].startswith("Mês inválido na data do teste: use um mês de 1 a 12.")


def test_formato_da_resposta_continua_o_do_fastapi(usuario_logado):
    # O frontend (lib/erros.ts) le detail[0].msg: a lista, o loc e o type
    # precisam continuar no mesmo lugar.
    resposta = usuario_logado.post("/tipos", json={})

    assert resposta.status_code == 422
    detalhes = resposta.json()["detail"]
    assert [(erro["type"], erro["loc"], erro["msg"]) for erro in detalhes] == [
        ("missing", ["body", "nome"], "Nome: campo obrigatório."),
        ("missing", ["body", "estoque_minimo"], "Estoque mínimo: campo obrigatório."),
    ]


def test_json_malformado_tem_mensagem_em_portugues(usuario_logado):
    resposta = usuario_logado.post(
        "/tipos", content="{nao e json", headers={"Content-Type": "application/json"}
    )

    erro = _primeiro_erro(resposta)
    assert erro["msg"] == "Requisição inválida: o corpo não é um JSON válido."


def test_corpo_ausente_tem_mensagem_em_portugues(usuario_logado):
    erro = _primeiro_erro(usuario_logado.post("/tipos"))

    assert erro["msg"] == "Requisição inválida: o corpo da requisição é obrigatório."


# --- Traducao isolada ---


def test_campo_sem_rotulo_usa_o_nome_tecnico():
    erro = {"type": "missing", "loc": ("body", "campo_novo"), "msg": "Field required"}

    assert traduzir_erro(erro) == "campo_novo: campo obrigatório."


def test_minimo_de_caracteres_maior_que_um():
    erro = {
        "type": "string_too_short",
        "loc": ("body", "senha"),
        "msg": "String should have at least 8 characters",
        "ctx": {"min_length": 8},
    }

    assert traduzir_erro(erro) == "Senha: deve ter pelo menos 8 caracteres."

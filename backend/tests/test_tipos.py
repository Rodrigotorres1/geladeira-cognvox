import uuid

import pytest

from auxiliares import mes_ano


def test_listar_tipos_sem_login_retorna_401(client):
    assert client.get("/tipos").status_code == 401


def test_criar_tipo_usa_validade_padrao_de_10_anos(usuario_logado):
    resposta = usuario_logado.post("/tipos", json={"nome": "Cilindro 10L", "estoque_minimo": 2})

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["nome"] == "Cilindro 10L"
    assert corpo["estoque_minimo"] == 2
    assert corpo["validade_anos"] == 10
    assert "dias_alerta" not in corpo
    assert corpo["estoque_disponivel"] == 0
    assert corpo["estoque_baixo"] is True


def test_criar_tipo_sem_estoque_minimo_retorna_422(usuario_logado):
    resposta = usuario_logado.post("/tipos", json={"nome": "Cilindro"})

    assert resposta.status_code == 422
    assert resposta.json()["detail"][0]["msg"] == "Estoque mínimo: campo obrigatório."


def test_criar_tipo_com_estoque_minimo_negativo_retorna_422(usuario_logado):
    resposta = usuario_logado.post("/tipos", json={"nome": "Cilindro", "estoque_minimo": -1})

    assert resposta.status_code == 422


def test_criar_tipo_com_validade_zero_ou_negativa_retorna_422(usuario_logado):
    for validade in (0, -5):
        resposta = usuario_logado.post(
            "/tipos", json={"nome": "Cilindro", "estoque_minimo": 1, "validade_anos": validade}
        )
        assert resposta.status_code == 422, validade


def test_criar_tipo_com_nome_repetido_retorna_409(usuario_logado, criar_tipo):
    criar_tipo(nome="Cilindro 10L")

    resposta = usuario_logado.post("/tipos", json={"nome": "Cilindro 10L", "estoque_minimo": 1})

    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "Já existe um tipo de cilindro com esse nome"


def test_atualizar_tipo(usuario_logado, tipo_criado):
    resposta = usuario_logado.put(
        f"/tipos/{tipo_criado['id']}",
        json={"nome": "Cilindro 15L", "estoque_minimo": 5, "validade_anos": 5},
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["nome"] == "Cilindro 15L"
    assert corpo["estoque_minimo"] == 5
    assert corpo["validade_anos"] == 5


def test_atualizar_tipo_mantendo_o_proprio_nome_funciona(usuario_logado, tipo_criado):
    resposta = usuario_logado.put(
        f"/tipos/{tipo_criado['id']}",
        json={"nome": tipo_criado["nome"], "estoque_minimo": 7, "validade_anos": 5},
    )

    assert resposta.status_code == 200
    assert resposta.json()["estoque_minimo"] == 7
    assert resposta.json()["validade_anos"] == 5


def test_atualizar_tipo_sem_validade_anos_retorna_422_e_nao_muda_nada(usuario_logado, criar_tipo):
    tipo = criar_tipo(validade_anos=5)

    resposta = usuario_logado.put(
        f"/tipos/{tipo['id']}", json={"nome": tipo["nome"], "estoque_minimo": 7}
    )

    assert resposta.status_code == 422
    erro = resposta.json()["detail"][0]
    assert erro["loc"] == ["body", "validade_anos"]
    assert erro["msg"] == "Validade (anos): campo obrigatório."
    tipo_atual = usuario_logado.get("/tipos").json()[0]
    assert tipo_atual["validade_anos"] == 5
    assert tipo_atual["estoque_minimo"] == tipo["estoque_minimo"]


def test_atualizar_tipo_para_nome_de_outro_retorna_409(usuario_logado, criar_tipo):
    criar_tipo(nome="Cilindro 10L")
    outro = criar_tipo(nome="Cilindro 15L")

    resposta = usuario_logado.put(
        f"/tipos/{outro['id']}",
        json={"nome": "Cilindro 10L", "estoque_minimo": 1, "validade_anos": 10},
    )

    assert resposta.status_code == 409


def test_atualizar_tipo_inexistente_retorna_404(usuario_logado):
    resposta = usuario_logado.put(
        f"/tipos/{uuid.uuid4()}",
        json={"nome": "Cilindro", "estoque_minimo": 1, "validade_anos": 10},
    )

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Tipo de cilindro não encontrado"


def test_mudar_validade_do_tipo_recalcula_vencimento_dos_lotes(
    usuario_logado, criar_tipo, entrada
):
    tipo = criar_tipo(nome="Cilindro 10L", estoque_minimo=1, validade_anos=10)
    entrada(tipo["id"], data_teste="04/2016", quantidade=3)

    resposta = usuario_logado.put(
        f"/tipos/{tipo['id']}",
        json={"nome": "Cilindro 10L", "estoque_minimo": 1, "validade_anos": 5},
    )

    assert resposta.json()["estoque_disponivel"] == 0
    lote = usuario_logado.get("/lotes").json()[0]
    assert lote["vencimento"] == "04/2021"
    assert lote["status"] == "vencido"


def test_excluir_tipo_sem_lotes_funciona(usuario_logado, tipo_criado):
    resposta = usuario_logado.delete(f"/tipos/{tipo_criado['id']}")

    assert resposta.status_code == 204
    assert usuario_logado.get("/tipos").json() == []


def test_excluir_tipo_com_lote_retorna_409(usuario_logado, tipo_criado, entrada):
    entrada(tipo_criado["id"])

    resposta = usuario_logado.delete(f"/tipos/{tipo_criado['id']}")

    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "Não é possível excluir um tipo que já tem lotes registrados"
    assert len(usuario_logado.get("/tipos").json()) == 1


def test_excluir_tipo_com_lote_zerado_tambem_retorna_409(usuario_logado, tipo_criado, entrada):
    lote_id = entrada(tipo_criado["id"], quantidade=3)["lote"]["id"]
    usuario_logado.post("/movimentacoes/saida", json={"lote_id": lote_id, "quantidade": 3})

    resposta = usuario_logado.delete(f"/tipos/{tipo_criado['id']}")

    assert resposta.status_code == 409


def test_excluir_tipo_inexistente_retorna_404(usuario_logado):
    resposta = usuario_logado.delete(f"/tipos/{uuid.uuid4()}")

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Tipo de cilindro não encontrado"


def _buscar_tipo(client, tipo_id):
    return next(tipo for tipo in client.get("/tipos").json() if tipo["id"] == tipo_id)


def test_estoque_disponivel_ignora_lotes_vencidos(usuario_logado, criar_tipo, entrada):
    # validade de 1 ano: teste de 13 meses atras ja venceu (no mes passado);
    # teste de 12 meses atras vence este mes e ainda pode ser usado.
    tipo = criar_tipo(estoque_minimo=5, validade_anos=1)
    entrada(tipo["id"], data_teste=mes_ano(-13), quantidade=10)
    entrada(tipo["id"], data_teste=mes_ano(-12), quantidade=3)

    tipo_atual = _buscar_tipo(usuario_logado, tipo["id"])

    assert tipo_atual["estoque_disponivel"] == 3
    assert tipo_atual["estoque_baixo"] is True


def test_estoque_nao_fica_baixo_quando_disponivel_atinge_o_minimo(
    usuario_logado, criar_tipo, entrada
):
    tipo = criar_tipo(estoque_minimo=5, validade_anos=1)
    entrada(tipo["id"], data_teste=mes_ano(-13), quantidade=10)
    entrada(tipo["id"], data_teste=mes_ano(0), quantidade=5)

    tipo_atual = _buscar_tipo(usuario_logado, tipo["id"])

    assert tipo_atual["estoque_disponivel"] == 5
    assert tipo_atual["estoque_baixo"] is False


def test_estoque_baixo_volta_quando_saida_deixa_abaixo_do_minimo(
    usuario_logado, criar_tipo, entrada
):
    tipo = criar_tipo(estoque_minimo=5)
    lote_id = entrada(tipo["id"], quantidade=5)["lote"]["id"]
    usuario_logado.post("/movimentacoes/saida", json={"lote_id": lote_id, "quantidade": 1})

    assert _buscar_tipo(usuario_logado, tipo["id"])["estoque_baixo"] is True


def test_listar_tipos_ordena_por_nome(usuario_logado, criar_tipo):
    criar_tipo(nome="Cilindro 15L")
    criar_tipo(nome="Cilindro 10L")

    nomes = [tipo["nome"] for tipo in usuario_logado.get("/tipos").json()]

    assert nomes == ["Cilindro 10L", "Cilindro 15L"]


# --- Nome do tipo ---


def test_nome_do_tipo_e_gravado_sem_espacos_nas_pontas(usuario_logado):
    resposta = usuario_logado.post(
        "/tipos", json={"nome": "  Cilindro 10L  ", "estoque_minimo": 1}
    )

    assert resposta.status_code == 201
    assert resposta.json()["nome"] == "Cilindro 10L"


@pytest.mark.parametrize("nome", ["", "   "])
def test_nome_vazio_ou_so_com_espacos_retorna_422(usuario_logado, nome):
    resposta = usuario_logado.post("/tipos", json={"nome": nome, "estoque_minimo": 1})

    assert resposta.status_code == 422
    assert resposta.json()["detail"][0]["msg"] == "Nome: não pode ficar em branco."
    assert usuario_logado.get("/tipos").json() == []


def test_atualizar_para_nome_so_com_espacos_retorna_422(usuario_logado, tipo_criado):
    resposta = usuario_logado.put(
        f"/tipos/{tipo_criado['id']}",
        json={"nome": "   ", "estoque_minimo": 1, "validade_anos": 10},
    )

    assert resposta.status_code == 422


@pytest.mark.parametrize(
    "existente, novo",
    [
        ("Cilindro 10L", "cilindro 10l"),
        ("Cilindro 10L", "  CILINDRO 10L "),
        ("Óxigênio Médico", "ÓXIGÊNIO MÉDICO"),
    ],
)
def test_nome_repetido_sem_diferenciar_maiusculas_retorna_409(
    usuario_logado, criar_tipo, existente, novo
):
    criar_tipo(nome=existente)

    resposta = usuario_logado.post("/tipos", json={"nome": novo, "estoque_minimo": 1})

    assert resposta.status_code == 409
    assert len(usuario_logado.get("/tipos").json()) == 1


def test_atualizar_para_nome_de_outro_com_outra_caixa_retorna_409(usuario_logado, criar_tipo):
    criar_tipo(nome="Cilindro 10L")
    outro = criar_tipo(nome="Cilindro 15L")

    resposta = usuario_logado.put(
        f"/tipos/{outro['id']}",
        json={"nome": "CILINDRO 10L", "estoque_minimo": 1, "validade_anos": 10},
    )

    assert resposta.status_code == 409


def test_atualizar_mudando_so_a_caixa_do_proprio_nome_funciona(usuario_logado, criar_tipo):
    tipo = criar_tipo(nome="cilindro 10l")

    resposta = usuario_logado.put(
        f"/tipos/{tipo['id']}",
        json={"nome": "Cilindro 10L", "estoque_minimo": 1, "validade_anos": 10},
    )

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Cilindro 10L"


def test_id_do_tipo_e_uuid_v4(tipo_criado):
    assert uuid.UUID(tipo_criado["id"]).version == 4

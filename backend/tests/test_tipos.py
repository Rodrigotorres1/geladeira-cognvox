import uuid


def test_listar_tipos_sem_login_retorna_401(client):
    assert client.get("/tipos").status_code == 401


def test_criar_tipo_usa_dias_alerta_padrao_de_30(usuario_logado):
    resposta = usuario_logado.post("/tipos", json={"nome": "Cilindro 10L", "estoque_minimo": 2})

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["nome"] == "Cilindro 10L"
    assert corpo["estoque_minimo"] == 2
    assert corpo["dias_alerta"] == 30
    assert corpo["estoque_disponivel"] == 0
    assert corpo["estoque_baixo"] is True


def test_criar_tipo_com_estoque_minimo_negativo_retorna_422(usuario_logado):
    resposta = usuario_logado.post("/tipos", json={"nome": "Cilindro", "estoque_minimo": -1})

    assert resposta.status_code == 422


def test_criar_tipo_com_nome_repetido_retorna_409(usuario_logado, criar_tipo):
    criar_tipo(nome="Cilindro 10L")

    resposta = usuario_logado.post("/tipos", json={"nome": "Cilindro 10L", "estoque_minimo": 1})

    assert resposta.status_code == 409


def test_atualizar_tipo(usuario_logado, tipo_criado):
    resposta = usuario_logado.put(
        f"/tipos/{tipo_criado['id']}",
        json={"nome": "Cilindro 15L", "estoque_minimo": 5, "dias_alerta": 10},
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["nome"] == "Cilindro 15L"
    assert corpo["estoque_minimo"] == 5
    assert corpo["dias_alerta"] == 10


def test_atualizar_tipo_mantendo_o_proprio_nome_funciona(usuario_logado, tipo_criado):
    resposta = usuario_logado.put(
        f"/tipos/{tipo_criado['id']}",
        json={"nome": tipo_criado["nome"], "estoque_minimo": 7},
    )

    assert resposta.status_code == 200


def test_atualizar_tipo_para_nome_de_outro_retorna_409(usuario_logado, criar_tipo):
    criar_tipo(nome="Cilindro 10L")
    outro = criar_tipo(nome="Cilindro 15L")

    resposta = usuario_logado.put(
        f"/tipos/{outro['id']}", json={"nome": "Cilindro 10L", "estoque_minimo": 1}
    )

    assert resposta.status_code == 409


def test_atualizar_tipo_inexistente_retorna_404(usuario_logado):
    resposta = usuario_logado.put(
        f"/tipos/{uuid.uuid4()}", json={"nome": "Cilindro", "estoque_minimo": 1}
    )

    assert resposta.status_code == 404


def test_excluir_tipo_sem_lotes_funciona(usuario_logado, tipo_criado):
    resposta = usuario_logado.delete(f"/tipos/{tipo_criado['id']}")

    assert resposta.status_code == 204
    assert usuario_logado.get("/tipos").json() == []


def test_excluir_tipo_com_lote_retorna_409(usuario_logado, tipo_criado, entrada):
    entrada(tipo_criado["id"])

    resposta = usuario_logado.delete(f"/tipos/{tipo_criado['id']}")

    assert resposta.status_code == 409
    assert len(usuario_logado.get("/tipos").json()) == 1


def test_excluir_tipo_com_lote_zerado_tambem_retorna_409(usuario_logado, tipo_criado, entrada):
    lote_id = entrada(tipo_criado["id"], quantidade=3)["lote"]["id"]
    usuario_logado.post("/movimentacoes/saida", json={"lote_id": lote_id, "quantidade": 3})

    resposta = usuario_logado.delete(f"/tipos/{tipo_criado['id']}")

    assert resposta.status_code == 409


def test_excluir_tipo_inexistente_retorna_404(usuario_logado):
    assert usuario_logado.delete(f"/tipos/{uuid.uuid4()}").status_code == 404


def _buscar_tipo(client, tipo_id):
    return next(tipo for tipo in client.get("/tipos").json() if tipo["id"] == tipo_id)


def test_estoque_disponivel_ignora_lotes_vencidos(usuario_logado, criar_tipo, entrada):
    tipo = criar_tipo(estoque_minimo=5)
    entrada(tipo["id"], quantidade=10, vencimento_em_dias=-1)
    entrada(tipo["id"], quantidade=3, vencimento_em_dias=0)

    tipo_atual = _buscar_tipo(usuario_logado, tipo["id"])

    assert tipo_atual["estoque_disponivel"] == 3
    assert tipo_atual["estoque_baixo"] is True


def test_estoque_nao_fica_baixo_quando_disponivel_atinge_o_minimo(
    usuario_logado, criar_tipo, entrada
):
    tipo = criar_tipo(estoque_minimo=5)
    entrada(tipo["id"], quantidade=10, vencimento_em_dias=-1)
    entrada(tipo["id"], quantidade=5, vencimento_em_dias=60)

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


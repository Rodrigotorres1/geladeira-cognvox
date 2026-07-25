def test_saida_diminui_a_quantidade_em_estoque(usuario_logado, item_criado):
    item_id = item_criado["id"]
    quantidade_inicial = item_criado["quantidade"]

    resposta = usuario_logado.post(
        "/movimentacoes", json={"item_id": item_id, "tipo": "saida", "quantidade": 3}
    )
    assert resposta.status_code == 201

    item_atualizado = next(
        item for item in usuario_logado.get("/itens").json() if item["id"] == item_id
    )
    assert item_atualizado["quantidade"] == quantidade_inicial - 3


def test_saida_aparece_no_relatorio_de_gastos(usuario_logado, item_criado):
    item_id = item_criado["id"]
    valor_unitario = float(item_criado["valor_unitario"])

    usuario_logado.post(
        "/movimentacoes", json={"item_id": item_id, "tipo": "saida", "quantidade": 3}
    )

    relatorio = usuario_logado.get("/relatorios/gastos").json()

    assert float(relatorio["total_gasto"]) == valor_unitario * 3
    assert any(mov["item_id"] == item_id for mov in relatorio["movimentacoes"])


def test_saida_maior_que_o_estoque_e_bloqueada(usuario_logado, item_criado):
    resposta = usuario_logado.post(
        "/movimentacoes",
        json={"item_id": item_criado["id"], "tipo": "saida", "quantidade": 999},
    )

    assert resposta.status_code == 400

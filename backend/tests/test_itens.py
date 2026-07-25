def test_listar_itens_sem_login_retorna_401(client):
    resposta = client.get("/itens")

    assert resposta.status_code == 401


def test_excluir_item_com_movimentacoes_retorna_409_e_preserva_historico(
    usuario_logado, item_criado
):
    item_id = item_criado["id"]
    usuario_logado.post(
        "/movimentacoes", json={"item_id": item_id, "tipo": "saida", "quantidade": 1}
    )

    resposta = usuario_logado.delete(f"/itens/{item_id}")

    assert resposta.status_code == 409

    # o item e a movimentacao continuam existindo — nada foi apagado
    itens = usuario_logado.get("/itens").json()
    assert any(item["id"] == item_id for item in itens)

    relatorio = usuario_logado.get("/relatorios/gastos").json()
    assert any(mov["item_id"] == item_id for mov in relatorio["movimentacoes"])


def test_excluir_item_sem_movimentacoes_funciona_normalmente(usuario_logado, item_criado):
    resposta = usuario_logado.delete(f"/itens/{item_criado['id']}")

    assert resposta.status_code == 204

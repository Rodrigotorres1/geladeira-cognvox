import pytest


def test_health_responde_sem_login(client):
    resposta = client.get("/health")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


@pytest.mark.parametrize("rota", ["/relatorios/gastos", "/itens"])
def test_rotas_da_base_antiga_nao_existem(usuario_logado, rota):
    assert usuario_logado.get(rota).status_code == 404


@pytest.mark.parametrize("metodo", ["delete", "put", "patch"])
def test_nao_existe_rota_para_editar_ou_excluir_movimentacao(
    usuario_logado, lote_com_estoque, metodo
):
    historico = usuario_logado.get("/movimentacoes").json()
    mov_id = historico[0]["id"]

    resposta = getattr(usuario_logado, metodo)(f"/movimentacoes/{mov_id}")

    assert resposta.status_code in (404, 405)
    assert usuario_logado.get("/movimentacoes").json() == historico


@pytest.mark.parametrize("metodo", ["delete", "put", "patch"])
def test_nao_existe_rota_de_estorno_na_colecao_de_movimentacoes(usuario_logado, metodo):
    resposta = getattr(usuario_logado, metodo)("/movimentacoes")

    assert resposta.status_code == 405


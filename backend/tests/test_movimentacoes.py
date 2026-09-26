import uuid

import pytest

from auxiliares import mes_ano


def _lotes(client):
    return client.get("/lotes").json()


def _post_entrada(client, tipo_id, data_teste, quantidade=1):
    return client.post(
        "/movimentacoes/entrada",
        json={"tipo_id": tipo_id, "data_teste": data_teste, "quantidade": quantidade},
    )


def test_movimentacoes_sem_login_retornam_401(client):
    assert client.get("/movimentacoes").status_code == 401
    assert client.post("/movimentacoes/entrada", json={}).status_code == 401
    assert client.post("/movimentacoes/saida", json={}).status_code == 401


# --- Entrada ---


def test_entrada_cria_lote_novo(usuario_logado, tipo_criado):
    resposta = usuario_logado.post(
        "/movimentacoes/entrada",
        json={
            "tipo_id": tipo_criado["id"],
            "data_teste": "04/2020",
            "quantidade": 4,
            "numero_lote": "L-001",
            "observacao": "Compra inicial",
        },
    )

    assert resposta.status_code == 201
    movimentacao = resposta.json()
    assert movimentacao["tipo"] == "entrada"
    assert movimentacao["quantidade"] == 4
    assert movimentacao["observacao"] == "Compra inicial"
    assert movimentacao["lote"]["tipo"]["nome"] == tipo_criado["nome"]
    assert movimentacao["lote"]["data_teste"] == "04/2020"
    assert movimentacao["lote"]["vencimento"] == "04/2030"

    lotes = _lotes(usuario_logado)
    assert len(lotes) == 1
    assert lotes[0]["quantidade"] == 4
    assert lotes[0]["numero_lote"] == "L-001"


def test_entrada_com_mesmo_tipo_e_data_do_teste_soma_no_lote(
    usuario_logado, tipo_criado, entrada
):
    primeira = entrada(tipo_criado["id"], data_teste="04/2020", quantidade=4)
    segunda = entrada(tipo_criado["id"], data_teste="4/2020", quantidade=6)

    assert primeira["lote"]["id"] == segunda["lote"]["id"]
    lotes = _lotes(usuario_logado)
    assert len(lotes) == 1
    assert lotes[0]["quantidade"] == 10


def test_entrada_so_com_ano_repetido_soma_no_lote(usuario_logado, tipo_criado, entrada):
    entrada(tipo_criado["id"], data_teste="2016", quantidade=2)
    entrada(tipo_criado["id"], data_teste="2016", quantidade=3)

    lotes = _lotes(usuario_logado)
    assert len(lotes) == 1
    assert lotes[0]["quantidade"] == 5


def test_entrada_com_data_do_teste_diferente_cria_outro_lote(
    usuario_logado, tipo_criado, entrada
):
    entrada(tipo_criado["id"], data_teste="04/2020", quantidade=4)
    entrada(tipo_criado["id"], data_teste="05/2020", quantidade=6)

    assert [lote["quantidade"] for lote in _lotes(usuario_logado)] == [4, 6]


def test_teste_so_com_ano_e_janeiro_do_mesmo_ano_sao_lotes_separados(
    usuario_logado, tipo_criado, entrada
):
    so_ano = entrada(tipo_criado["id"], data_teste="2016", quantidade=2)
    janeiro = entrada(tipo_criado["id"], data_teste="01/2016", quantidade=3)

    assert so_ano["lote"]["id"] != janeiro["lote"]["id"]
    lotes = {lote["data_teste"]: lote for lote in _lotes(usuario_logado)}
    assert lotes["2016"]["quantidade"] == 2
    assert lotes["2016"]["vencimento"] == "01/2026"
    assert lotes["01/2016"]["quantidade"] == 3
    assert lotes["01/2016"]["vencimento"] == "01/2026"


def test_mesma_data_do_teste_em_tipos_diferentes_sao_lotes_diferentes(
    usuario_logado, criar_tipo, entrada
):
    tipo_a = criar_tipo(nome="Cilindro 10L")
    tipo_b = criar_tipo(nome="Cilindro 15L")
    entrada(tipo_a["id"], data_teste="04/2020")
    entrada(tipo_b["id"], data_teste="04/2020")

    assert len(_lotes(usuario_logado)) == 2


def test_entrada_que_soma_mantem_o_numero_de_lote_original(usuario_logado, tipo_criado, entrada):
    entrada(tipo_criado["id"], numero_lote="ORIGINAL")
    entrada(tipo_criado["id"], numero_lote="OUTRO")

    assert _lotes(usuario_logado)[0]["numero_lote"] == "ORIGINAL"


def test_entrada_que_soma_preenche_numero_de_lote_vazio(usuario_logado, tipo_criado, entrada):
    entrada(tipo_criado["id"])
    entrada(tipo_criado["id"], numero_lote="NOVO")

    assert _lotes(usuario_logado)[0]["numero_lote"] == "NOVO"


def test_entrada_em_lote_zerado_reaproveita_o_lote(usuario_logado, tipo_criado, entrada):
    lote_id = entrada(tipo_criado["id"], quantidade=2)["lote"]["id"]
    usuario_logado.post("/movimentacoes/saida", json={"lote_id": lote_id, "quantidade": 2})

    nova = entrada(tipo_criado["id"], quantidade=3)

    assert nova["lote"]["id"] == lote_id
    assert _lotes(usuario_logado)[0]["quantidade"] == 3


def test_entrada_de_lote_ja_vencido_e_aceita(usuario_logado, tipo_criado, entrada):
    entrada(tipo_criado["id"], data_teste="04/2010")

    assert _lotes(usuario_logado)[0]["status"] == "vencido"


def test_entrada_de_tipo_inexistente_retorna_404(usuario_logado):
    resposta = _post_entrada(usuario_logado, str(uuid.uuid4()), "04/2020")

    assert resposta.status_code == 404


@pytest.mark.parametrize("data_teste", ["04/2026", "4/2026", "2026"])
def test_entrada_aceita_os_formatos_de_data_do_teste(usuario_logado, tipo_criado, data_teste):
    resposta = _post_entrada(usuario_logado, tipo_criado["id"], data_teste)

    assert resposta.status_code == 201


@pytest.mark.parametrize(
    "data_teste, trecho_da_mensagem",
    [
        ("13/2026", "Mês inválido na data do teste: use um mês de 1 a 12"),
        ("0/2026", "1 a 12"),
        ("26", "Data do teste inválida. Use MM/AAAA, M/AAAA ou AAAA"),
        ("04/26", "MM/AAAA, M/AAAA ou AAAA"),
        ("", "MM/AAAA, M/AAAA ou AAAA"),
        ("abril de 2020", "MM/AAAA, M/AAAA ou AAAA"),
        (None, "MM/AAAA, M/AAAA ou AAAA"),
        (2020, "MM/AAAA, M/AAAA ou AAAA"),
    ],
)
def test_entrada_com_data_do_teste_invalida_retorna_422_com_mensagem(
    usuario_logado, tipo_criado, data_teste, trecho_da_mensagem
):
    resposta = _post_entrada(usuario_logado, tipo_criado["id"], data_teste)

    assert resposta.status_code == 422
    erro = resposta.json()["detail"][0]
    assert erro["loc"] == ["body", "data_teste"]
    assert trecho_da_mensagem in erro["msg"]
    assert _lotes(usuario_logado) == []


@pytest.mark.parametrize("meses_a_frente", [1, 12])
def test_entrada_com_data_do_teste_no_futuro_retorna_422(
    usuario_logado, tipo_criado, meses_a_frente
):
    resposta = _post_entrada(usuario_logado, tipo_criado["id"], mes_ano(meses_a_frente))

    assert resposta.status_code == 422
    assert resposta.json()["detail"][0]["msg"] == "A data do teste não pode estar no futuro."


def test_entrada_com_ano_seguinte_so_com_ano_retorna_422(usuario_logado, tipo_criado):
    ano_que_vem = mes_ano(12).split("/")[1]

    resposta = _post_entrada(usuario_logado, tipo_criado["id"], ano_que_vem)

    assert resposta.status_code == 422


def test_entrada_com_quantidade_zero_negativa_ou_fracionada_retorna_422(
    usuario_logado, tipo_criado
):
    for quantidade in (0, -1, 1.5):
        resposta = _post_entrada(usuario_logado, tipo_criado["id"], "04/2020", quantidade)
        assert resposta.status_code == 422, quantidade

    assert _lotes(usuario_logado) == []


# --- Saida ---


def test_saida_diminui_a_quantidade_do_lote(usuario_logado, lote_com_estoque):
    resposta = usuario_logado.post(
        "/movimentacoes/saida",
        json={"lote_id": lote_com_estoque["id"], "quantidade": 3, "observacao": "Paciente X"},
    )

    assert resposta.status_code == 201
    assert resposta.json()["tipo"] == "saida"
    assert resposta.json()["observacao"] == "Paciente X"
    assert _lotes(usuario_logado)[0]["quantidade"] == lote_com_estoque["quantidade"] - 3


def test_saida_maior_que_o_lote_retorna_400_e_nao_altera_nada(usuario_logado, lote_com_estoque):
    resposta = usuario_logado.post(
        "/movimentacoes/saida",
        json={"lote_id": lote_com_estoque["id"], "quantidade": lote_com_estoque["quantidade"] + 1},
    )

    assert resposta.status_code == 400
    assert resposta.json()["detail"] == "Quantidade maior que a disponível no lote"
    assert _lotes(usuario_logado)[0]["quantidade"] == lote_com_estoque["quantidade"]
    tipos = [mov["tipo"] for mov in usuario_logado.get("/movimentacoes").json()]
    assert tipos == ["entrada"]


def test_saida_considera_so_o_lote_escolhido_e_nao_o_total_do_tipo(
    usuario_logado, tipo_criado, entrada
):
    lote_pequeno = entrada(tipo_criado["id"], data_teste="04/2020", quantidade=2)["lote"]
    entrada(tipo_criado["id"], data_teste="05/2020", quantidade=10)

    resposta = usuario_logado.post(
        "/movimentacoes/saida", json={"lote_id": lote_pequeno["id"], "quantidade": 3}
    )

    assert resposta.status_code == 400


def test_saida_de_lote_vencido_e_permitida(usuario_logado, tipo_criado, entrada):
    lote_id = entrada(tipo_criado["id"], data_teste="04/2010", quantidade=5)["lote"]["id"]

    resposta = usuario_logado.post(
        "/movimentacoes/saida", json={"lote_id": lote_id, "quantidade": 5}
    )

    assert resposta.status_code == 201


def test_saida_de_lote_inexistente_retorna_404(usuario_logado):
    resposta = usuario_logado.post(
        "/movimentacoes/saida", json={"lote_id": str(uuid.uuid4()), "quantidade": 1}
    )

    assert resposta.status_code == 404


def test_saida_com_quantidade_zero_retorna_422(usuario_logado, lote_com_estoque):
    resposta = usuario_logado.post(
        "/movimentacoes/saida", json={"lote_id": lote_com_estoque["id"], "quantidade": 0}
    )

    assert resposta.status_code == 422


def test_reteste_e_saida_do_lote_antigo_mais_entrada_com_a_nova_data(
    usuario_logado, tipo_criado, entrada
):
    antigo = entrada(tipo_criado["id"], data_teste="04/2010", quantidade=2)["lote"]

    usuario_logado.post(
        "/movimentacoes/saida",
        json={"lote_id": antigo["id"], "quantidade": 2, "observacao": "Enviado para reteste"},
    )
    novo = entrada(tipo_criado["id"], data_teste=mes_ano(0), quantidade=2)["lote"]

    lotes = _lotes(usuario_logado)
    assert [lote["id"] for lote in lotes] == [novo["id"]]
    assert lotes[0]["status"] == "ok"


# --- Lote zerado e historico ---


def test_lote_zerado_some_da_listagem_e_continua_no_historico(usuario_logado, lote_com_estoque):
    lote_id = lote_com_estoque["id"]
    usuario_logado.post(
        "/movimentacoes/saida",
        json={"lote_id": lote_id, "quantidade": lote_com_estoque["quantidade"]},
    )

    assert _lotes(usuario_logado) == []

    historico = usuario_logado.get("/movimentacoes").json()
    assert len(historico) == 2
    assert all(mov["lote"]["id"] == lote_id for mov in historico)
    assert {mov["tipo"] for mov in historico} == {"entrada", "saida"}


def test_historico_registra_a_usuaria_e_os_dados_do_lote(usuario_logado, tipo_criado, entrada):
    entrada(tipo_criado["id"], data_teste="2016", numero_lote="L-9")
    usuaria_id = usuario_logado.get("/auth/me").json()["id"]

    mov = usuario_logado.get("/movimentacoes").json()[0]

    assert mov["usuario_id"] == usuaria_id
    assert mov["lote"]["data_teste"] == "2016"
    assert mov["lote"]["vencimento"] == "01/2026"
    assert mov["lote"]["numero_lote"] == "L-9"
    assert mov["lote"]["tipo"]["id"] == tipo_criado["id"]


def test_historico_vem_do_mais_recente_para_o_mais_antigo(usuario_logado, lote_com_estoque):
    for quantidade in (1, 2, 3):
        usuario_logado.post(
            "/movimentacoes/saida",
            json={"lote_id": lote_com_estoque["id"], "quantidade": quantidade},
        )

    historico = usuario_logado.get("/movimentacoes").json()

    assert [mov["quantidade"] for mov in historico] == [3, 2, 1, 10]
    datas = [mov["criado_em"] for mov in historico]
    assert datas == sorted(datas, reverse=True)

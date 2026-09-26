import uuid

from auxiliares import dias


def _lotes(client):
    return client.get("/lotes").json()


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
            "data_vencimento": dias(90),
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

    lotes = _lotes(usuario_logado)
    assert len(lotes) == 1
    assert lotes[0]["quantidade"] == 4
    assert lotes[0]["data_vencimento"] == dias(90)
    assert lotes[0]["numero_lote"] == "L-001"


def test_entrada_com_mesmo_tipo_e_vencimento_soma_no_lote(usuario_logado, tipo_criado, entrada):
    primeira = entrada(tipo_criado["id"], quantidade=4, vencimento_em_dias=90)
    segunda = entrada(tipo_criado["id"], quantidade=6, vencimento_em_dias=90)

    assert primeira["lote"]["id"] == segunda["lote"]["id"]
    lotes = _lotes(usuario_logado)
    assert len(lotes) == 1
    assert lotes[0]["quantidade"] == 10


def test_entrada_com_vencimento_diferente_cria_outro_lote(usuario_logado, tipo_criado, entrada):
    entrada(tipo_criado["id"], quantidade=4, vencimento_em_dias=90)
    entrada(tipo_criado["id"], quantidade=6, vencimento_em_dias=120)

    assert [lote["quantidade"] for lote in _lotes(usuario_logado)] == [4, 6]


def test_mesmo_vencimento_em_tipos_diferentes_sao_lotes_diferentes(
    usuario_logado, criar_tipo, entrada
):
    tipo_a = criar_tipo(nome="Cilindro 10L")
    tipo_b = criar_tipo(nome="Cilindro 15L")
    entrada(tipo_a["id"], vencimento_em_dias=90)
    entrada(tipo_b["id"], vencimento_em_dias=90)

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


def test_entrada_com_vencimento_no_passado_e_aceita_e_nasce_vencida(
    usuario_logado, tipo_criado, entrada
):
    entrada(tipo_criado["id"], vencimento_em_dias=-10)

    assert _lotes(usuario_logado)[0]["status"] == "vencido"


def test_entrada_de_tipo_inexistente_retorna_404(usuario_logado):
    resposta = usuario_logado.post(
        "/movimentacoes/entrada",
        json={"tipo_id": str(uuid.uuid4()), "data_vencimento": dias(90), "quantidade": 1},
    )

    assert resposta.status_code == 404


def test_entrada_com_quantidade_zero_negativa_ou_fracionada_retorna_422(
    usuario_logado, tipo_criado
):
    for quantidade in (0, -1, 1.5):
        resposta = usuario_logado.post(
            "/movimentacoes/entrada",
            json={
                "tipo_id": tipo_criado["id"],
                "data_vencimento": dias(90),
                "quantidade": quantidade,
            },
        )
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
    assert _lotes(usuario_logado)[0]["quantidade"] == lote_com_estoque["quantidade"]
    tipos = [mov["tipo"] for mov in usuario_logado.get("/movimentacoes").json()]
    assert tipos == ["entrada"]


def test_saida_considera_so_o_lote_escolhido_e_nao_o_total_do_tipo(
    usuario_logado, tipo_criado, entrada
):
    lote_pequeno = entrada(tipo_criado["id"], quantidade=2, vencimento_em_dias=30)["lote"]
    entrada(tipo_criado["id"], quantidade=10, vencimento_em_dias=60)

    resposta = usuario_logado.post(
        "/movimentacoes/saida", json={"lote_id": lote_pequeno["id"], "quantidade": 3}
    )

    assert resposta.status_code == 400


def test_saida_de_lote_vencido_e_permitida(usuario_logado, tipo_criado, entrada):
    lote_id = entrada(tipo_criado["id"], quantidade=5, vencimento_em_dias=-1)["lote"]["id"]

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


def test_historico_registra_a_usuaria_e_os_dados_do_lote(
    usuario_logado, tipo_criado, entrada
):
    entrada(tipo_criado["id"], vencimento_em_dias=90, numero_lote="L-9")
    usuaria_id = usuario_logado.get("/auth/me").json()["id"]

    mov = usuario_logado.get("/movimentacoes").json()[0]

    assert mov["usuario_id"] == usuaria_id
    assert mov["lote"]["data_vencimento"] == dias(90)
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

import uuid

from auxiliares import dias


def test_listar_lotes_sem_login_retorna_401(client):
    assert client.get("/lotes").status_code == 401


def test_listar_lotes_ordena_por_vencimento(usuario_logado, criar_tipo, entrada):
    tipo_a = criar_tipo(nome="Cilindro 10L")
    tipo_b = criar_tipo(nome="Cilindro 15L")
    entrada(tipo_a["id"], vencimento_em_dias=90)
    entrada(tipo_b["id"], vencimento_em_dias=10)
    entrada(tipo_a["id"], vencimento_em_dias=45)

    vencimentos = [lote["data_vencimento"] for lote in usuario_logado.get("/lotes").json()]

    assert vencimentos == [dias(10), dias(45), dias(90)]


def test_listar_lotes_filtra_por_tipo(usuario_logado, criar_tipo, entrada):
    tipo_a = criar_tipo(nome="Cilindro 10L")
    tipo_b = criar_tipo(nome="Cilindro 15L")
    entrada(tipo_a["id"])
    entrada(tipo_b["id"])

    lotes = usuario_logado.get("/lotes", params={"tipo_id": tipo_a["id"]}).json()

    assert len(lotes) == 1
    assert lotes[0]["tipo"] == {"id": tipo_a["id"], "nome": "Cilindro 10L"}


def test_status_do_lote_usa_dias_alerta_do_tipo(usuario_logado, criar_tipo, entrada):
    tipo = criar_tipo(dias_alerta=15)
    entrada(tipo["id"], vencimento_em_dias=-1)
    entrada(tipo["id"], vencimento_em_dias=15)
    entrada(tipo["id"], vencimento_em_dias=16)

    status = [lote["status"] for lote in usuario_logado.get("/lotes").json()]

    assert status == ["vencido", "vence_em_breve", "ok"]


def test_editar_vencimento_e_numero_do_lote(usuario_logado, lote_com_estoque):
    resposta = usuario_logado.put(
        f"/lotes/{lote_com_estoque['id']}",
        json={"data_vencimento": dias(120), "numero_lote": "ABC-123"},
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["data_vencimento"] == dias(120)
    assert corpo["numero_lote"] == "ABC-123"
    assert corpo["quantidade"] == lote_com_estoque["quantidade"]

    lote_listado = usuario_logado.get("/lotes").json()[0]
    assert lote_listado["data_vencimento"] == dias(120)
    assert lote_listado["numero_lote"] == "ABC-123"


def test_editar_so_o_numero_mantendo_a_data_nao_conflita_consigo_mesmo(
    usuario_logado, lote_com_estoque
):
    resposta = usuario_logado.put(
        f"/lotes/{lote_com_estoque['id']}",
        json={"data_vencimento": lote_com_estoque["data_vencimento"], "numero_lote": "XYZ"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["numero_lote"] == "XYZ"


def test_editar_numero_do_lote_para_vazio_limpa_o_campo(usuario_logado, tipo_criado, entrada):
    lote_id = entrada(tipo_criado["id"], numero_lote="ABC")["lote"]["id"]

    resposta = usuario_logado.put(
        f"/lotes/{lote_id}", json={"data_vencimento": dias(90), "numero_lote": ""}
    )

    assert resposta.status_code == 200
    assert resposta.json()["numero_lote"] is None


def test_editar_vencimento_para_data_de_outro_lote_do_mesmo_tipo_retorna_409(
    usuario_logado, tipo_criado, entrada
):
    lote_a = entrada(tipo_criado["id"], vencimento_em_dias=30)["lote"]
    entrada(tipo_criado["id"], vencimento_em_dias=60)

    resposta = usuario_logado.put(
        f"/lotes/{lote_a['id']}", json={"data_vencimento": dias(60), "numero_lote": None}
    )

    assert resposta.status_code == 409
    # nada mudou: continuam dois lotes, cada um com sua data
    vencimentos = [lote["data_vencimento"] for lote in usuario_logado.get("/lotes").json()]
    assert vencimentos == [dias(30), dias(60)]


def test_editar_vencimento_para_data_de_lote_zerado_do_mesmo_tipo_retorna_409(
    usuario_logado, tipo_criado, entrada
):
    lote_zerado = entrada(tipo_criado["id"], quantidade=2, vencimento_em_dias=60)["lote"]
    usuario_logado.post(
        "/movimentacoes/saida", json={"lote_id": lote_zerado["id"], "quantidade": 2}
    )
    lote_a = entrada(tipo_criado["id"], vencimento_em_dias=30)["lote"]

    resposta = usuario_logado.put(
        f"/lotes/{lote_a['id']}", json={"data_vencimento": dias(60)}
    )

    assert resposta.status_code == 409


def test_editar_vencimento_para_data_de_lote_de_outro_tipo_e_permitido(
    usuario_logado, criar_tipo, entrada
):
    tipo_a = criar_tipo(nome="Cilindro 10L")
    tipo_b = criar_tipo(nome="Cilindro 15L")
    lote_a = entrada(tipo_a["id"], vencimento_em_dias=30)["lote"]
    entrada(tipo_b["id"], vencimento_em_dias=60)

    resposta = usuario_logado.put(
        f"/lotes/{lote_a['id']}", json={"data_vencimento": dias(60)}
    )

    assert resposta.status_code == 200


def test_editar_lote_inexistente_retorna_404(usuario_logado):
    resposta = usuario_logado.put(f"/lotes/{uuid.uuid4()}", json={"data_vencimento": dias(30)})

    assert resposta.status_code == 404


def test_nao_existe_rota_para_excluir_lote(usuario_logado, lote_com_estoque):
    resposta = usuario_logado.delete(f"/lotes/{lote_com_estoque['id']}")

    assert resposta.status_code == 405
    assert len(usuario_logado.get("/lotes").json()) == 1


def test_nao_existe_rota_para_criar_lote_direto(usuario_logado, tipo_criado):
    resposta = usuario_logado.post(
        "/lotes",
        json={"tipo_id": tipo_criado["id"], "data_vencimento": dias(30), "quantidade": 5},
    )

    assert resposta.status_code == 405

import uuid

from auxiliares import mes_ano


def _detalhe_422(resposta):
    return resposta.json()["detail"][0]["msg"]


def test_listar_lotes_sem_login_retorna_401(client):
    assert client.get("/lotes").status_code == 401


def test_lote_devolve_data_do_teste_como_digitada_e_vencimento_sempre_com_mes(
    usuario_logado, tipo_criado, entrada
):
    entrada(tipo_criado["id"], data_teste="4/2016")
    entrada(tipo_criado["id"], data_teste="2017")

    lotes = usuario_logado.get("/lotes").json()

    assert [(lote["data_teste"], lote["vencimento"]) for lote in lotes] == [
        ("04/2016", "04/2026"),
        ("2017", "01/2027"),
    ]


def test_listar_lotes_ordena_pelo_vencimento_e_nao_pela_data_do_teste(
    usuario_logado, criar_tipo, entrada
):
    tipo_10_anos = criar_tipo(nome="Cilindro 10L", validade_anos=10)
    tipo_5_anos = criar_tipo(nome="Cilindro 15L", validade_anos=5)
    entrada(tipo_10_anos["id"], data_teste="01/2020")  # vence 01/2030
    entrada(tipo_5_anos["id"], data_teste="01/2022")  # vence 01/2027
    entrada(tipo_10_anos["id"], data_teste="06/2019")  # vence 06/2029

    vencimentos = [lote["vencimento"] for lote in usuario_logado.get("/lotes").json()]

    assert vencimentos == ["01/2027", "06/2029", "01/2030"]


def test_listar_lotes_filtra_por_tipo(usuario_logado, criar_tipo, entrada):
    tipo_a = criar_tipo(nome="Cilindro 10L")
    tipo_b = criar_tipo(nome="Cilindro 15L")
    entrada(tipo_a["id"])
    entrada(tipo_b["id"])

    lotes = usuario_logado.get("/lotes", params={"tipo_id": tipo_a["id"]}).json()

    assert len(lotes) == 1
    assert lotes[0]["tipo"] == {"id": tipo_a["id"], "nome": "Cilindro 10L"}


def test_status_e_meses_restantes_do_lote(usuario_logado, criar_tipo, entrada):
    # validade de 1 ano: vencimento = data do teste + 12 meses
    tipo = criar_tipo(validade_anos=1)
    entrada(tipo["id"], data_teste=mes_ano(-13))  # venceu mes passado
    entrada(tipo["id"], data_teste=mes_ano(-12))  # vence este mes
    entrada(tipo["id"], data_teste=mes_ano(-10))  # faltam 2 meses
    entrada(tipo["id"], data_teste=mes_ano(-9))  # faltam 3 meses
    entrada(tipo["id"], data_teste=mes_ano(-6))  # faltam 6 meses
    entrada(tipo["id"], data_teste=mes_ano(-5))  # faltam 7 meses

    lotes = usuario_logado.get("/lotes").json()

    assert [(lote["meses_restantes"], lote["status"]) for lote in lotes] == [
        (-1, "vencido"),
        (0, "urgente"),
        (2, "urgente"),
        (3, "atencao"),
        (6, "atencao"),
        (7, "ok"),
    ]


def test_editar_data_do_teste_e_numero_do_lote(usuario_logado, lote_com_estoque):
    resposta = usuario_logado.put(
        f"/lotes/{lote_com_estoque['id']}",
        json={"data_teste": "03/2020", "numero_lote": "ABC-123"},
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["data_teste"] == "03/2020"
    assert corpo["vencimento"] == "03/2030"
    assert corpo["numero_lote"] == "ABC-123"
    assert corpo["quantidade"] == lote_com_estoque["quantidade"]

    lote_listado = usuario_logado.get("/lotes").json()[0]
    assert lote_listado["data_teste"] == "03/2020"
    assert lote_listado["numero_lote"] == "ABC-123"


def test_editar_data_do_teste_para_so_ano(usuario_logado, lote_com_estoque):
    resposta = usuario_logado.put(
        f"/lotes/{lote_com_estoque['id']}", json={"data_teste": "2019"}
    )

    assert resposta.status_code == 200
    assert resposta.json()["data_teste"] == "2019"
    assert resposta.json()["vencimento"] == "01/2029"


def test_editar_so_o_numero_mantendo_a_data_nao_conflita_consigo_mesmo(
    usuario_logado, lote_com_estoque
):
    resposta = usuario_logado.put(
        f"/lotes/{lote_com_estoque['id']}",
        json={"data_teste": lote_com_estoque["data_teste"], "numero_lote": "XYZ"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["numero_lote"] == "XYZ"


def test_editar_numero_do_lote_para_vazio_limpa_o_campo(usuario_logado, tipo_criado, entrada):
    lote_id = entrada(tipo_criado["id"], data_teste="04/2016", numero_lote="ABC")["lote"]["id"]

    resposta = usuario_logado.put(
        f"/lotes/{lote_id}", json={"data_teste": "04/2016", "numero_lote": ""}
    )

    assert resposta.status_code == 200
    assert resposta.json()["numero_lote"] is None


def test_editar_data_do_teste_para_a_de_outro_lote_do_mesmo_tipo_retorna_409(
    usuario_logado, tipo_criado, entrada
):
    lote_a = entrada(tipo_criado["id"], data_teste="03/2020")["lote"]
    entrada(tipo_criado["id"], data_teste="06/2020")

    resposta = usuario_logado.put(f"/lotes/{lote_a['id']}", json={"data_teste": "6/2020"})

    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "Já existe outro lote desse tipo com essa data de teste"
    # nada mudou: continuam dois lotes, cada um com sua data
    datas = [lote["data_teste"] for lote in usuario_logado.get("/lotes").json()]
    assert datas == ["03/2020", "06/2020"]


def test_editar_para_data_de_lote_zerado_do_mesmo_tipo_retorna_409(
    usuario_logado, tipo_criado, entrada
):
    lote_zerado = entrada(tipo_criado["id"], data_teste="06/2020", quantidade=2)["lote"]
    usuario_logado.post(
        "/movimentacoes/saida", json={"lote_id": lote_zerado["id"], "quantidade": 2}
    )
    lote_a = entrada(tipo_criado["id"], data_teste="03/2020")["lote"]

    resposta = usuario_logado.put(f"/lotes/{lote_a['id']}", json={"data_teste": "06/2020"})

    assert resposta.status_code == 409


def test_editar_de_mes_para_so_ano_do_mesmo_janeiro_nao_conflita(
    usuario_logado, tipo_criado, entrada
):
    # "2016" e "01/2016" sao lotes diferentes, entao nao ha colisao
    lote_a = entrada(tipo_criado["id"], data_teste="03/2016")["lote"]
    entrada(tipo_criado["id"], data_teste="01/2016")

    resposta = usuario_logado.put(f"/lotes/{lote_a['id']}", json={"data_teste": "2016"})

    assert resposta.status_code == 200


def test_editar_para_data_de_lote_de_outro_tipo_e_permitido(usuario_logado, criar_tipo, entrada):
    tipo_a = criar_tipo(nome="Cilindro 10L")
    tipo_b = criar_tipo(nome="Cilindro 15L")
    lote_a = entrada(tipo_a["id"], data_teste="03/2020")["lote"]
    entrada(tipo_b["id"], data_teste="06/2020")

    resposta = usuario_logado.put(f"/lotes/{lote_a['id']}", json={"data_teste": "06/2020"})

    assert resposta.status_code == 200


def test_editar_com_data_do_teste_invalida_retorna_422(usuario_logado, lote_com_estoque):
    resposta = usuario_logado.put(
        f"/lotes/{lote_com_estoque['id']}", json={"data_teste": "13/2020"}
    )

    assert resposta.status_code == 422
    assert "Mês inválido" in _detalhe_422(resposta)


def test_editar_com_data_do_teste_no_futuro_retorna_422(usuario_logado, lote_com_estoque):
    resposta = usuario_logado.put(
        f"/lotes/{lote_com_estoque['id']}", json={"data_teste": mes_ano(1)}
    )

    assert resposta.status_code == 422
    assert "não pode estar no futuro" in _detalhe_422(resposta)


def test_editar_lote_inexistente_retorna_404(usuario_logado):
    resposta = usuario_logado.put(f"/lotes/{uuid.uuid4()}", json={"data_teste": "03/2020"})

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Lote não encontrado"


def test_nao_existe_rota_para_excluir_lote(usuario_logado, lote_com_estoque):
    resposta = usuario_logado.delete(f"/lotes/{lote_com_estoque['id']}")

    assert resposta.status_code == 405
    assert len(usuario_logado.get("/lotes").json()) == 1


def test_nao_existe_rota_para_criar_lote_direto(usuario_logado, tipo_criado):
    resposta = usuario_logado.post(
        "/lotes", json={"tipo_id": tipo_criado["id"], "data_teste": "03/2020", "quantidade": 5}
    )

    assert resposta.status_code == 405


def test_put_do_lote_ignora_quantidade(usuario_logado, lote_com_estoque):
    resposta = usuario_logado.put(
        f"/lotes/{lote_com_estoque['id']}",
        json={"data_teste": lote_com_estoque["data_teste"], "quantidade": 999},
    )

    assert resposta.status_code == 200
    assert resposta.json()["quantidade"] == lote_com_estoque["quantidade"]
    assert usuario_logado.get("/lotes").json()[0]["quantidade"] == lote_com_estoque["quantidade"]


def test_id_do_lote_e_uuid_v4(lote_com_estoque):
    assert uuid.UUID(lote_com_estoque["id"]).version == 4

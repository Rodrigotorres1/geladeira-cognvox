from datetime import date

import pytest

from app.services.data_teste import (
    DataTeste,
    DataTesteInvalidaError,
    formatar_data_teste,
    formatar_vencimento,
    interpretar_data_teste,
)

HOJE = date(2026, 9, 26)


@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("04/2026", DataTeste(date(2026, 4, 1), so_ano=False)),
        ("4/2026", DataTeste(date(2026, 4, 1), so_ano=False)),
        ("2026", DataTeste(date(2026, 1, 1), so_ano=True)),
        ("12/2016", DataTeste(date(2016, 12, 1), so_ano=False)),
        ("  04/2016  ", DataTeste(date(2016, 4, 1), so_ano=False)),
        # mes atual ainda nao e futuro
        ("09/2026", DataTeste(date(2026, 9, 1), so_ano=False)),
    ],
)
def test_formatos_aceitos(texto, esperado):
    assert interpretar_data_teste(texto, HOJE) == esperado


@pytest.mark.parametrize(
    "texto",
    ["13/2026", "0/2026", "26", "04/26", "", "   ", "abc", "04-2026", "2026/04", "04/2026/1"],
)
def test_formatos_recusados(texto):
    with pytest.raises(DataTesteInvalidaError):
        interpretar_data_teste(texto, HOJE)


@pytest.mark.parametrize("texto", ["10/2026", "2027", "1/2030"])
def test_data_no_futuro_e_recusada(texto):
    with pytest.raises(DataTesteInvalidaError, match="futuro"):
        interpretar_data_teste(texto, HOJE)


def test_mensagem_de_formato_invalido_diz_os_formatos_aceitos():
    with pytest.raises(DataTesteInvalidaError) as erro:
        interpretar_data_teste("04/26", HOJE)

    assert "MM/AAAA" in str(erro.value)
    assert "AAAA" in str(erro.value)


def test_formatar_devolve_no_formato_digitado():
    assert formatar_data_teste(date(2016, 4, 1), so_ano=False) == "04/2016"
    assert formatar_data_teste(date(2016, 1, 1), so_ano=True) == "2016"


def test_vencimento_sempre_sai_com_mes():
    assert formatar_vencimento(date(2026, 1, 1)) == "01/2026"
    assert formatar_vencimento(date(2026, 4, 1)) == "04/2026"


def test_mensagens_de_erro_tem_acentuacao():
    with pytest.raises(DataTesteInvalidaError, match="Mês inválido"):
        interpretar_data_teste("13/2020", HOJE)
    with pytest.raises(DataTesteInvalidaError, match="não pode estar no futuro"):
        interpretar_data_teste("2030", HOJE)
    with pytest.raises(DataTesteInvalidaError, match="Data do teste inválida"):
        interpretar_data_teste("abc", HOJE)


def test_ano_anterior_a_1900_e_recusado_e_1900_e_aceito():
    with pytest.raises(DataTesteInvalidaError, match="Ano inválido"):
        interpretar_data_teste("1899", HOJE)
    with pytest.raises(DataTesteInvalidaError, match="Ano inválido"):
        interpretar_data_teste("12/1899", HOJE)

    assert interpretar_data_teste("1900", HOJE) == DataTeste(date(1900, 1, 1), so_ano=True)

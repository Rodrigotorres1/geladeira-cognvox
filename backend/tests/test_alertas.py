from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from app.services.alertas import (
    QuantidadeVencimento,
    data_hoje,
    estoque_baixo,
    estoque_disponivel,
    meses_restantes,
    status_lote,
)
from app.services.data_teste import calcular_vencimento, formatar_vencimento

# Teste hidrostatico em 04/2016, validade de 10 anos -> vence em 04/2026.
VENCIMENTO_ABRIL_2026 = calcular_vencimento(date(2016, 4, 1), 10)

# Teste so com ano "2016" (gravado como janeiro) -> vence em 01/2026.
VENCIMENTO_SO_ANO_2016 = calcular_vencimento(date(2016, 1, 1), 10)


def test_vencimento_e_data_do_teste_mais_validade():
    assert VENCIMENTO_ABRIL_2026 == date(2026, 4, 1)
    assert formatar_vencimento(VENCIMENTO_ABRIL_2026) == "04/2026"


def test_vencimento_do_teste_so_com_ano_e_janeiro_e_sai_com_mes():
    assert VENCIMENTO_SO_ANO_2016 == date(2026, 1, 1)
    assert formatar_vencimento(VENCIMENTO_SO_ANO_2016) == "01/2026"


def test_meses_restantes_ignora_o_dia():
    assert meses_restantes(date(2026, 4, 1), date(2026, 4, 30)) == 0
    assert meses_restantes(date(2026, 4, 1), date(2026, 5, 1)) == -1
    assert meses_restantes(date(2026, 4, 1), date(2025, 9, 15)) == 7
    assert meses_restantes(date(2027, 1, 1), date(2026, 12, 31)) == 1


@pytest.mark.parametrize(
    "hoje, esperado",
    [
        (date(2025, 9, 1), "ok"),
        (date(2025, 9, 30), "ok"),
        (date(2025, 10, 1), "atencao"),
        (date(2025, 12, 15), "atencao"),
        (date(2026, 1, 31), "atencao"),
        (date(2026, 2, 1), "urgente"),
        (date(2026, 3, 15), "urgente"),
        (date(2026, 4, 1), "urgente"),
        # pode ser usado ate o fim do mes de vencimento
        (date(2026, 4, 30), "urgente"),
        (date(2026, 5, 1), "vencido"),
        (date(2027, 1, 1), "vencido"),
    ],
)
def test_status_do_lote_testado_em_04_2016(hoje, esperado):
    assert status_lote(VENCIMENTO_ABRIL_2026, hoje) == esperado


@pytest.mark.parametrize(
    "hoje, esperado",
    [
        (date(2025, 6, 30), "ok"),
        (date(2025, 7, 1), "atencao"),
        (date(2025, 10, 31), "atencao"),
        (date(2025, 11, 1), "urgente"),
        (date(2026, 1, 31), "urgente"),
        (date(2026, 2, 1), "vencido"),
    ],
)
def test_status_do_lote_testado_so_com_ano_2016(hoje, esperado):
    assert status_lote(VENCIMENTO_SO_ANO_2016, hoje) == esperado


def test_estoque_disponivel_ignora_lotes_vencidos():
    hoje = date(2026, 4, 15)
    lotes = [
        QuantidadeVencimento(quantidade=4, vencimento=date(2026, 3, 1)),  # vencido
        QuantidadeVencimento(quantidade=3, vencimento=date(2026, 4, 1)),  # vence este mes
        QuantidadeVencimento(quantidade=5, vencimento=date(2030, 1, 1)),
    ]

    assert estoque_disponivel(lotes, hoje) == 8


def test_estoque_disponivel_sem_lotes_e_zero():
    assert estoque_disponivel([], date(2026, 4, 15)) == 0


def test_estoque_baixo_quando_disponivel_menor_que_minimo():
    assert estoque_baixo(estoque_disponivel=2, estoque_minimo=3) is True


def test_estoque_nao_esta_baixo_quando_disponivel_igual_ao_minimo():
    assert estoque_baixo(estoque_disponivel=3, estoque_minimo=3) is False


def test_estoque_minimo_zero_nunca_fica_baixo():
    assert estoque_baixo(estoque_disponivel=0, estoque_minimo=0) is False


def test_data_hoje_usa_o_fuso_configurado():
    assert data_hoje() == datetime.now(ZoneInfo("America/Sao_Paulo")).date()

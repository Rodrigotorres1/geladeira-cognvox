from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.services.alertas import data_hoje, estoque_baixo, estoque_disponivel, status_lote

HOJE = date(2026, 9, 26)


@dataclass
class LoteFake:
    quantidade: int
    data_vencimento: date


def test_lote_com_vencimento_anterior_a_hoje_esta_vencido():
    assert status_lote(HOJE - timedelta(days=1), dias_alerta=30, hoje=HOJE) == "vencido"


def test_lote_que_vence_hoje_vence_em_breve_e_nao_esta_vencido():
    assert status_lote(HOJE, dias_alerta=30, hoje=HOJE) == "vence_em_breve"


def test_lote_que_vence_exatamente_em_dias_alerta_vence_em_breve():
    assert status_lote(HOJE + timedelta(days=30), dias_alerta=30, hoje=HOJE) == "vence_em_breve"


def test_lote_que_vence_um_dia_depois_de_dias_alerta_esta_ok():
    assert status_lote(HOJE + timedelta(days=31), dias_alerta=30, hoje=HOJE) == "ok"


def test_dias_alerta_zero_so_alerta_no_proprio_dia():
    assert status_lote(HOJE, dias_alerta=0, hoje=HOJE) == "vence_em_breve"
    assert status_lote(HOJE + timedelta(days=1), dias_alerta=0, hoje=HOJE) == "ok"


def test_dias_alerta_do_tipo_e_respeitado():
    vencimento = HOJE + timedelta(days=10)

    assert status_lote(vencimento, dias_alerta=7, hoje=HOJE) == "ok"
    assert status_lote(vencimento, dias_alerta=10, hoje=HOJE) == "vence_em_breve"


def test_estoque_disponivel_ignora_lotes_vencidos():
    lotes = [
        LoteFake(quantidade=4, data_vencimento=HOJE - timedelta(days=1)),
        LoteFake(quantidade=3, data_vencimento=HOJE),
        LoteFake(quantidade=5, data_vencimento=HOJE + timedelta(days=90)),
    ]

    assert estoque_disponivel(lotes, HOJE) == 8


def test_estoque_disponivel_sem_lotes_e_zero():
    assert estoque_disponivel([], HOJE) == 0


def test_estoque_baixo_quando_disponivel_menor_que_minimo():
    assert estoque_baixo(estoque_disponivel=2, estoque_minimo=3) is True


def test_estoque_nao_esta_baixo_quando_disponivel_igual_ao_minimo():
    assert estoque_baixo(estoque_disponivel=3, estoque_minimo=3) is False


def test_estoque_minimo_zero_nunca_fica_baixo():
    assert estoque_baixo(estoque_disponivel=0, estoque_minimo=0) is False


def test_data_hoje_usa_o_fuso_configurado():
    assert data_hoje() == datetime.now(ZoneInfo("America/Sao_Paulo")).date()

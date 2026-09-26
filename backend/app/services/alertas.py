from datetime import date, datetime
from typing import Iterable, Literal, NamedTuple
from zoneinfo import ZoneInfo

from app.core.config import get_settings

StatusLote = Literal["vencido", "urgente", "atencao", "ok"]


class QuantidadeVencimento(NamedTuple):
    quantidade: int
    vencimento: date


# Todas as regras de alerta recebem `hoje` como parametro em vez de chamar
# data_hoje() por dentro: assim os testes fixam a data e cobrem as bordas
# (virada de mes, ultimo dia do mes de vencimento) sem depender do relogio.


def data_hoje() -> date:
    return datetime.now(ZoneInfo(get_settings().timezone)).date()


def meses_restantes(vencimento: date, hoje: date) -> int:
    # Conta em meses de calendario, ignorando o dia: o vencimento do teste
    # hidrostatico e mes/ano, e o cilindro vale ate o fim do mes de vencimento.
    return (vencimento.year * 12 + vencimento.month) - (hoje.year * 12 + hoje.month)


def status_lote(vencimento: date, hoje: date) -> StatusLote:
    settings = get_settings()
    meses = meses_restantes(vencimento, hoje)
    if meses < 0:
        return "vencido"
    if meses <= settings.meses_alerta_urgente:
        return "urgente"
    if meses <= settings.meses_alerta_atencao:
        return "atencao"
    return "ok"


def estoque_disponivel(lotes: Iterable[QuantidadeVencimento], hoje: date) -> int:
    # Lote vencido continua existindo (e pode sair do estoque), mas nao conta
    # como cilindro disponivel para uso.
    return sum(
        lote.quantidade for lote in lotes if status_lote(lote.vencimento, hoje) != "vencido"
    )


def estoque_baixo(estoque_disponivel: int, estoque_minimo: int) -> bool:
    return estoque_disponivel < estoque_minimo

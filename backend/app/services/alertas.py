from datetime import date, datetime
from typing import Iterable, Literal, Protocol
from zoneinfo import ZoneInfo

from app.core.config import get_settings

StatusLote = Literal["vencido", "vence_em_breve", "ok"]


class LoteComVencimento(Protocol):
    quantidade: int
    data_vencimento: date


# Todas as regras de alerta recebem `hoje` como parametro em vez de chamar
# data_hoje() por dentro: assim os testes fixam a data e cobrem as bordas
# (vence hoje, vence exatamente em dias_alerta) sem depender do relogio.


def data_hoje() -> date:
    return datetime.now(ZoneInfo(get_settings().timezone)).date()


def status_lote(data_vencimento: date, dias_alerta: int, hoje: date) -> StatusLote:
    if data_vencimento < hoje:
        return "vencido"
    if (data_vencimento - hoje).days <= dias_alerta:
        return "vence_em_breve"
    return "ok"


def estoque_disponivel(lotes: Iterable[LoteComVencimento], hoje: date) -> int:
    # Lote vencido continua existindo (e pode sair do estoque), mas nao conta
    # como cilindro disponivel para uso.
    return sum(lote.quantidade for lote in lotes if lote.data_vencimento >= hoje)


def estoque_baixo(estoque_disponivel: int, estoque_minimo: int) -> bool:
    return estoque_disponivel < estoque_minimo

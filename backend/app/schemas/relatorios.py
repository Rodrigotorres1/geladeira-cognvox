import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.movimentacoes import MovimentacaoOut


class RelatorioGastos(BaseModel):
    usuario_id: uuid.UUID
    data_inicio: date
    data_fim: date
    total_gasto: Decimal
    movimentacoes: list[MovimentacaoOut]

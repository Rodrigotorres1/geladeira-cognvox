import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.movimentacao import TipoMovimentacao


class MovimentacaoCriar(BaseModel):
    item_id: uuid.UUID
    tipo: TipoMovimentacao
    quantidade: float = Field(gt=0)


class MovimentacaoOut(BaseModel):
    id: uuid.UUID
    item_id: uuid.UUID
    usuario_id: uuid.UUID
    tipo: TipoMovimentacao
    quantidade: float
    valor_total: Decimal
    criado_em: datetime

    model_config = {"from_attributes": True}

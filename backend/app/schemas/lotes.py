import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.comum import TextoOpcional
from app.schemas.tipos import TipoResumo
from app.services.alertas import StatusLote


class LoteAtualizar(BaseModel):
    # Quantidade nao e editavel: correcao de quantidade e sempre uma
    # entrada/saida com observacao, para ficar no historico.
    data_vencimento: date
    numero_lote: TextoOpcional = None


class LoteOut(BaseModel):
    id: uuid.UUID
    tipo: TipoResumo
    quantidade: int
    data_vencimento: date
    numero_lote: Optional[str] = None
    criado_em: datetime
    # Calculado em lotes_service com os dias_alerta do tipo (nao fica no banco).
    status: StatusLote


class LoteResumo(BaseModel):
    id: uuid.UUID
    tipo: TipoResumo
    data_vencimento: date
    numero_lote: Optional[str] = None

    model_config = {"from_attributes": True}

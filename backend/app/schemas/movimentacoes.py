import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.movimentacao import TipoMovimentacao
from app.schemas.comum import TextoOpcional
from app.schemas.lotes import LoteResumo


class EntradaCriar(BaseModel):
    # A entrada nao aponta para um lote: o lote e encontrado (ou criado)
    # pelo par tipo + vencimento em registrar_entrada.
    tipo_id: uuid.UUID
    data_vencimento: date
    quantidade: int = Field(gt=0)
    numero_lote: TextoOpcional = None
    observacao: TextoOpcional = None


class SaidaCriar(BaseModel):
    lote_id: uuid.UUID
    quantidade: int = Field(gt=0)
    observacao: TextoOpcional = None


class MovimentacaoOut(BaseModel):
    id: uuid.UUID
    lote: LoteResumo
    usuario_id: uuid.UUID
    tipo: TipoMovimentacao
    quantidade: int
    observacao: Optional[str] = None
    criado_em: datetime

    model_config = {"from_attributes": True}

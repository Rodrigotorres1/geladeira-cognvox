import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.movimentacao import TipoMovimentacao
from app.schemas.comum import TextoOpcional
from app.schemas.lotes import DataTesteEntrada, LoteResumo


class EntradaCriar(BaseModel):
    # A entrada nao aponta para um lote: o lote e encontrado (ou criado)
    # pelo trio tipo + data do teste (+ so ano) em registrar_entrada.
    tipo_id: uuid.UUID
    data_teste: DataTesteEntrada
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

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class ItemCriar(BaseModel):
    nome: str = Field(min_length=1)
    quantidade: float = Field(ge=0)
    unidade: str = Field(min_length=1)
    valor_unitario: Decimal = Field(ge=0)
    validade: Optional[date] = None


class ItemAtualizar(BaseModel):
    nome: str = Field(min_length=1)
    quantidade: float = Field(ge=0)
    unidade: str = Field(min_length=1)
    valor_unitario: Decimal = Field(ge=0)
    validade: Optional[date] = None


class ItemOut(BaseModel):
    id: uuid.UUID
    usuario_id: uuid.UUID
    nome: str
    quantidade: float
    unidade: str
    valor_unitario: Decimal
    validade: Optional[date] = None
    atualizado_em: datetime

    model_config = {"from_attributes": True}

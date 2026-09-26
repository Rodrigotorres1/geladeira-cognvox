import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TipoCriar(BaseModel):
    nome: str = Field(min_length=1)
    estoque_minimo: int = Field(ge=0)
    validade_anos: int = Field(default=10, gt=0)


TipoAtualizar = TipoCriar


class TipoOut(BaseModel):
    id: uuid.UUID
    nome: str
    estoque_minimo: int
    validade_anos: int
    criado_em: datetime
    # Calculados em tipos_service a partir dos lotes (nao ficam no banco).
    estoque_disponivel: int
    estoque_baixo: bool


class TipoResumo(BaseModel):
    id: uuid.UUID
    nome: str

    model_config = {"from_attributes": True}

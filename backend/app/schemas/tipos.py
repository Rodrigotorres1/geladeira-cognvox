import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

# Espacos nas pontas sao removidos antes de validar: "   " vira "" e cai no
# min_length (422), e "  Cilindro 10L " e gravado como "Cilindro 10L".
NomeTipo = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class TipoCriar(BaseModel):
    nome: NomeTipo
    estoque_minimo: int = Field(ge=0)
    validade_anos: int = Field(default=10, gt=0)


class TipoAtualizar(BaseModel):
    # PUT e substituicao completa: sem padrao para validade_anos, senao omitir
    # o campo voltaria a validade para 10 em silencio (e recalcularia o
    # vencimento de todos os lotes do tipo).
    nome: NomeTipo
    estoque_minimo: int = Field(ge=0)
    validade_anos: int = Field(gt=0)


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

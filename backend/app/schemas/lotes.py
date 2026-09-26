import uuid
from datetime import datetime
from typing import Annotated, Any, Optional

from pydantic import BaseModel, PlainValidator, WithJsonSchema
from pydantic_core import PydanticCustomError

from app.schemas.comum import TextoOpcional
from app.schemas.tipos import TipoResumo
from app.services.alertas import StatusLote, data_hoje
from app.services.data_teste import (
    FORMATOS_ACEITOS,
    DataTeste,
    DataTesteInvalidaError,
    interpretar_data_teste,
)


def _validar_data_teste(valor: Any) -> DataTeste:
    # PydanticCustomError em vez de ValueError: a mensagem chega no 422 sem o
    # prefixo "Value error, " que o pydantic poe nos ValueError.
    if not isinstance(valor, str):
        raise PydanticCustomError(
            "data_teste_invalida", f"Data do teste inválida. Use {FORMATOS_ACEITOS}."
        )
    try:
        return interpretar_data_teste(valor, data_hoje())
    except DataTesteInvalidaError as erro:
        raise PydanticCustomError("data_teste_invalida", str(erro))


# Chega como texto ("04/2016", "4/2016" ou "2016") e sai do schema ja
# interpretado; para a API/Swagger o campo continua sendo uma string.
DataTesteEntrada = Annotated[
    DataTeste,
    PlainValidator(_validar_data_teste),
    WithJsonSchema({"type": "string", "examples": ["04/2016", "2016"]}),
]


class LoteAtualizar(BaseModel):
    # Quantidade nao e editavel: correcao de quantidade e sempre uma
    # entrada/saida com observacao, para ficar no historico.
    data_teste: DataTesteEntrada
    numero_lote: TextoOpcional = None


class LoteOut(BaseModel):
    id: uuid.UUID
    tipo: TipoResumo
    quantidade: int
    # data_teste no formato em que a usuaria digitou ("04/2016" ou "2016");
    # vencimento sempre com mes ("2016" -> "01/2026").
    data_teste: str
    vencimento: str
    numero_lote: Optional[str] = None
    criado_em: datetime
    # Calculados em lotes_service (nao ficam no banco).
    meses_restantes: int
    status: StatusLote


class LoteResumo(BaseModel):
    id: uuid.UUID
    tipo: TipoResumo
    data_teste: str
    vencimento: str
    numero_lote: Optional[str] = None

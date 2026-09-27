from typing import Any

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Nome de cada campo como aparece na tela, para a mensagem dizer qual campo
# esta errado ("Quantidade: deve ser maior que 0."). Campo fora da lista
# aparece com o nome tecnico mesmo.
ROTULOS_CAMPOS = {
    "nome": "Nome",
    "email": "E-mail",
    "senha": "Senha",
    "estoque_minimo": "Estoque mínimo",
    "validade_anos": "Validade (anos)",
    "tipo_id": "Tipo de cilindro",
    "lote_id": "Lote",
    "data_teste": "Data do teste",
    "quantidade": "Quantidade",
    "numero_lote": "Nº do lote",
    "observacao": "Observação",
}

# Erros de validacao que ja nascem com mensagem em portugues (ver
# schemas/lotes.py:_validar_data_teste) e passam sem traducao.
TIPOS_JA_TRADUZIDOS = {"data_teste_invalida"}


def _descrever_erro(tipo: str, ctx: dict[str, Any]) -> str:
    if tipo == "missing":
        return "campo obrigatório."
    if tipo == "greater_than":
        return f"deve ser maior que {ctx['gt']}."
    if tipo == "greater_than_equal":
        return f"deve ser maior ou igual a {ctx['ge']}."
    if tipo in ("int_parsing", "int_from_float", "int_type"):
        return "informe um número inteiro."
    if tipo == "string_type":
        return "informe um texto."
    if tipo == "string_too_short":
        if ctx["min_length"] == 1:
            return "não pode ficar em branco."
        return f"deve ter pelo menos {ctx['min_length']} caracteres."
    if tipo == "string_too_long":
        return f"deve ter no máximo {ctx['max_length']} caracteres."
    if tipo == "json_invalid":
        return "o corpo não é um JSON válido."
    return "valor inválido."


def traduzir_erro(erro: dict[str, Any]) -> str:
    if erro["type"] in TIPOS_JA_TRADUZIDOS:
        return erro["msg"]

    # loc vem como ("body", "campo") ou ("query", "campo"). O campo e o ultimo
    # nome em texto depois da origem: numeros no loc sao posicao (item de
    # lista ou, no JSON malformado, o caractere onde o parse falhou).
    nomes = [parte for parte in erro["loc"][1:] if isinstance(parte, str)]
    campo = nomes[-1] if nomes else None
    descricao = _descrever_erro(erro["type"], erro.get("ctx") or {})
    if campo is None:
        if erro["type"] == "missing":
            return "Requisição inválida: o corpo da requisição é obrigatório."
        return f"Requisição inválida: {descricao}"
    rotulo = ROTULOS_CAMPOS.get(str(campo), str(campo))
    return f"{rotulo}: {descricao}"


async def tratar_erro_validacao(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Mesmo formato do handler padrao do FastAPI ({"detail": [{type, loc,
    # msg, ...}]}), so com "msg" em portugues: o frontend continua lendo
    # detail[0].msg (lib/erros.ts:extrairMensagemErro) sem mudanca.
    erros = []
    for erro in exc.errors():
        erros.append({**erro, "msg": traduzir_erro(erro)})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": jsonable_encoder(erros)},
    )

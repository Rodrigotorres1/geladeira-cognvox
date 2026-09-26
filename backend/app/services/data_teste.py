import re
from datetime import date
from typing import NamedTuple

FORMATOS_ACEITOS = "MM/AAAA, M/AAAA ou AAAA (ex.: 04/2016, 4/2016 ou 2016)"

_MES_ANO = re.compile(r"([0-9]{1,2})/([0-9]{4})")
_SO_ANO = re.compile(r"[0-9]{4}")


class DataTeste(NamedTuple):
    # Sempre dia 1: o teste hidrostatico e marcado no cilindro so com mes/ano
    # (ou so ano), entao o dia nao carrega informacao nenhuma.
    data: date
    so_ano: bool


class DataTesteInvalidaError(ValueError):
    pass


def interpretar_data_teste(texto: str, hoje: date) -> DataTeste:
    texto = texto.strip()

    if casamento := _MES_ANO.fullmatch(texto):
        mes, ano, so_ano = int(casamento[1]), int(casamento[2]), False
    elif _SO_ANO.fullmatch(texto):
        # So ano: assume janeiro, a leitura mais conservadora (vence antes).
        mes, ano, so_ano = 1, int(texto), True
    else:
        raise DataTesteInvalidaError(f"Data do teste inválida. Use {FORMATOS_ACEITOS}.")

    if not 1 <= mes <= 12:
        raise DataTesteInvalidaError(
            f"Mês inválido na data do teste: use um mês de 1 a 12. Formatos aceitos: {FORMATOS_ACEITOS}."
        )
    if ano < 1900:
        raise DataTesteInvalidaError("Ano inválido na data do teste.")

    data = date(ano, mes, 1)
    if data > hoje.replace(day=1):
        raise DataTesteInvalidaError("A data do teste não pode estar no futuro.")

    return DataTeste(data=data, so_ano=so_ano)


def formatar_data_teste(data: date, so_ano: bool) -> str:
    """Devolve a data do teste no formato em que a usuaria digitou: "2016"
    ou "04/2016"."""
    return str(data.year) if so_ano else formatar_vencimento(data)


def formatar_vencimento(vencimento: date) -> str:
    # Sempre com mes, mesmo quando o teste foi informado so com ano: o lote
    # "2016" vence em 01/2026, e mostrar so "2026" daria a entender que o
    # cilindro vale o ano inteiro.
    return f"{vencimento.month:02d}/{vencimento.year}"


def calcular_vencimento(data_teste: date, validade_anos: int) -> date:
    # data_teste e sempre dia 1, entao trocar o ano nunca cai em 29/02.
    return data_teste.replace(year=data_teste.year + validade_anos)

import uuid
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.lote import Lote
from app.schemas.lotes import LoteAtualizar, LoteOut, LoteResumo
from app.schemas.tipos import TipoResumo
from app.services import alertas
from app.services.data_teste import (
    calcular_vencimento,
    formatar_data_teste,
    formatar_vencimento,
)


class LoteNaoEncontradoError(Exception):
    pass


class LoteDuplicadoError(Exception):
    pass


def vencimento(lote: Lote) -> date:
    return calcular_vencimento(lote.data_teste, lote.tipo.validade_anos)


def montar_lote_resumo(lote: Lote) -> LoteResumo:
    return LoteResumo(
        id=lote.id,
        tipo=TipoResumo.model_validate(lote.tipo),
        data_teste=formatar_data_teste(lote.data_teste, lote.data_teste_so_ano),
        vencimento=formatar_vencimento(vencimento(lote)),
        numero_lote=lote.numero_lote,
    )


def montar_lote_out(lote: Lote, hoje: date) -> LoteOut:
    venc = vencimento(lote)
    return LoteOut(
        id=lote.id,
        tipo=TipoResumo.model_validate(lote.tipo),
        quantidade=lote.quantidade,
        data_teste=formatar_data_teste(lote.data_teste, lote.data_teste_so_ano),
        vencimento=formatar_vencimento(venc),
        numero_lote=lote.numero_lote,
        criado_em=lote.criado_em,
        meses_restantes=alertas.meses_restantes(venc, hoje),
        status=alertas.status_lote(venc, hoje),
    )


def listar(
    db: Session, tipo_id: Optional[uuid.UUID] = None, hoje: Optional[date] = None
) -> list[LoteOut]:
    hoje = hoje or alertas.data_hoje()
    # Lote zerado sai da listagem principal, mas continua no banco (e no
    # historico de movimentacoes, que aponta para ele).
    consulta = db.query(Lote).filter(Lote.quantidade > 0)
    if tipo_id is not None:
        consulta = consulta.filter(Lote.tipo_id == tipo_id)
    # Ordena em Python: o vencimento depende do validade_anos de cada tipo,
    # entao nao da para ordenar por data_teste no banco.
    lotes = sorted(consulta.all(), key=lambda lote: (vencimento(lote), lote.criado_em))
    return [montar_lote_out(lote, hoje) for lote in lotes]


def buscar(db: Session, lote_id: uuid.UUID) -> Lote:
    lote = db.get(Lote, lote_id)
    if lote is None:
        raise LoteNaoEncontradoError()
    return lote


def atualizar(db: Session, lote_id: uuid.UUID, dados: LoteAtualizar) -> LoteOut:
    lote = buscar(db, lote_id)

    # (tipo_id, data_teste, data_teste_so_ano) e unico: mudar a data para a
    # de outro lote do mesmo tipo fundiria dois lotes, entao e bloqueado.
    # Comparar com Lote.id != lote.id deixa editar so o numero_lote mantendo
    # a mesma data.
    conflito = (
        db.query(Lote.id)
        .filter(
            Lote.tipo_id == lote.tipo_id,
            Lote.data_teste == dados.data_teste.data,
            Lote.data_teste_so_ano == dados.data_teste.so_ano,
            Lote.id != lote.id,
        )
        .first()
    )
    if conflito is not None:
        raise LoteDuplicadoError()

    lote.data_teste = dados.data_teste.data
    lote.data_teste_so_ano = dados.data_teste.so_ano
    lote.numero_lote = dados.numero_lote
    db.commit()
    db.refresh(lote)
    return montar_lote_out(lote, alertas.data_hoje())

import uuid
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.lote import Lote
from app.schemas.lotes import LoteAtualizar, LoteOut
from app.schemas.tipos import TipoResumo
from app.services import alertas


class LoteNaoEncontradoError(Exception):
    pass


class LoteDuplicadoError(Exception):
    pass


def montar_lote_out(lote: Lote, hoje: date) -> LoteOut:
    return LoteOut(
        id=lote.id,
        tipo=TipoResumo.model_validate(lote.tipo),
        quantidade=lote.quantidade,
        data_vencimento=lote.data_vencimento,
        numero_lote=lote.numero_lote,
        criado_em=lote.criado_em,
        status=alertas.status_lote(lote.data_vencimento, lote.tipo.dias_alerta, hoje),
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
    lotes = consulta.order_by(Lote.data_vencimento, Lote.criado_em).all()
    return [montar_lote_out(lote, hoje) for lote in lotes]


def buscar(db: Session, lote_id: uuid.UUID) -> Lote:
    lote = db.get(Lote, lote_id)
    if lote is None:
        raise LoteNaoEncontradoError()
    return lote


def atualizar(db: Session, lote_id: uuid.UUID, dados: LoteAtualizar) -> LoteOut:
    lote = buscar(db, lote_id)

    # (tipo_id, data_vencimento) e unico: mudar a data para a de outro lote
    # do mesmo tipo fundiria dois lotes, entao e bloqueado. Comparar com
    # Lote.id != lote.id deixa editar so o numero_lote mantendo a mesma data.
    conflito = (
        db.query(Lote.id)
        .filter(
            Lote.tipo_id == lote.tipo_id,
            Lote.data_vencimento == dados.data_vencimento,
            Lote.id != lote.id,
        )
        .first()
    )
    if conflito is not None:
        raise LoteDuplicadoError()

    lote.data_vencimento = dados.data_vencimento
    lote.numero_lote = dados.numero_lote
    db.commit()
    db.refresh(lote)
    return montar_lote_out(lote, alertas.data_hoje())

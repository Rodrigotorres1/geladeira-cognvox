import uuid

from sqlalchemy.orm import Session

from app.models.lote import Lote
from app.models.movimentacao import Movimentacao, TipoMovimentacao
from app.schemas.movimentacoes import EntradaCriar, SaidaCriar
from app.services import lotes_service, tipos_service


class EstoqueInsuficienteError(Exception):
    pass


def registrar_entrada(
    db: Session, dados: EntradaCriar, usuario_id: uuid.UUID
) -> Movimentacao:
    # buscar levanta TipoNaoEncontradoError se o tipo nao existir.
    tipos_service.buscar(db, dados.tipo_id)

    lote = (
        db.query(Lote)
        .filter(Lote.tipo_id == dados.tipo_id, Lote.data_vencimento == dados.data_vencimento)
        .first()
    )
    if lote is None:
        lote = Lote(
            tipo_id=dados.tipo_id,
            data_vencimento=dados.data_vencimento,
            numero_lote=dados.numero_lote,
            quantidade=0,
        )
        db.add(lote)
    elif lote.numero_lote is None:
        # Lote ja existente mantem o numero_lote original; so e preenchido
        # se ainda nao tinha um.
        lote.numero_lote = dados.numero_lote

    lote.quantidade += dados.quantidade

    movimentacao = Movimentacao(
        lote=lote,
        usuario_id=usuario_id,
        tipo=TipoMovimentacao.ENTRADA,
        quantidade=dados.quantidade,
        observacao=dados.observacao,
    )
    db.add(movimentacao)
    db.commit()
    db.refresh(movimentacao)
    return movimentacao


def registrar_saida(db: Session, dados: SaidaCriar, usuario_id: uuid.UUID) -> Movimentacao:
    # buscar levanta LoteNaoEncontradoError se o lote nao existir.
    lote = lotes_service.buscar(db, dados.lote_id)

    # Lote vencido pode sair normalmente (descarte/devolucao): a unica
    # restricao e nao tirar mais do que o lote tem.
    if dados.quantidade > lote.quantidade:
        raise EstoqueInsuficienteError()

    lote.quantidade -= dados.quantidade

    movimentacao = Movimentacao(
        lote=lote,
        usuario_id=usuario_id,
        tipo=TipoMovimentacao.SAIDA,
        quantidade=dados.quantidade,
        observacao=dados.observacao,
    )
    db.add(movimentacao)
    db.commit()
    db.refresh(movimentacao)
    return movimentacao


def listar(db: Session) -> list[Movimentacao]:
    return db.query(Movimentacao).order_by(Movimentacao.criado_em.desc()).all()

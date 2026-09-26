import uuid

from sqlalchemy.orm import Session

from app.models.lote import Lote
from app.models.movimentacao import Movimentacao, TipoMovimentacao
from app.schemas.movimentacoes import EntradaCriar, MovimentacaoOut, SaidaCriar
from app.services import lotes_service, tipos_service


class EstoqueInsuficienteError(Exception):
    pass


def montar_movimentacao_out(movimentacao: Movimentacao) -> MovimentacaoOut:
    return MovimentacaoOut(
        id=movimentacao.id,
        lote=lotes_service.montar_lote_resumo(movimentacao.lote),
        usuario_id=movimentacao.usuario_id,
        tipo=movimentacao.tipo,
        quantidade=movimentacao.quantidade,
        observacao=movimentacao.observacao,
        criado_em=movimentacao.criado_em,
    )


def registrar_entrada(
    db: Session, dados: EntradaCriar, usuario_id: uuid.UUID
) -> MovimentacaoOut:
    # buscar levanta TipoNaoEncontradoError se o tipo nao existir.
    tipos_service.buscar(db, dados.tipo_id)

    lote = (
        db.query(Lote)
        .filter(
            Lote.tipo_id == dados.tipo_id,
            Lote.data_teste == dados.data_teste.data,
            Lote.data_teste_so_ano == dados.data_teste.so_ano,
        )
        .first()
    )
    if lote is None:
        lote = Lote(
            tipo_id=dados.tipo_id,
            data_teste=dados.data_teste.data,
            data_teste_so_ano=dados.data_teste.so_ano,
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
    return montar_movimentacao_out(movimentacao)


def registrar_saida(db: Session, dados: SaidaCriar, usuario_id: uuid.UUID) -> MovimentacaoOut:
    # buscar levanta LoteNaoEncontradoError se o lote nao existir.
    lote = lotes_service.buscar(db, dados.lote_id)

    # Lote vencido pode sair normalmente (descarte/reteste): a unica
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
    return montar_movimentacao_out(movimentacao)


def listar(db: Session) -> list[MovimentacaoOut]:
    movimentacoes = db.query(Movimentacao).order_by(Movimentacao.criado_em.desc()).all()
    return [montar_movimentacao_out(movimentacao) for movimentacao in movimentacoes]

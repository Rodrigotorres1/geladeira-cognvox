import calendar
import uuid
from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.movimentacao import Movimentacao, TipoMovimentacao
from app.schemas.movimentacoes import MovimentacaoCriar
from app.services import itens_service


class EstoqueInsuficienteError(Exception):
    pass


def registrar_movimentacao(
    db: Session, dados: MovimentacaoCriar, usuario_id: uuid.UUID
) -> Movimentacao:
    # buscar_item ja levanta ItemNaoEncontradoError se o item nao existir,
    # entao toda movimentacao so acontece se o item de fato existe.
    item = itens_service.buscar_item(db, dados.item_id)

    if dados.tipo == TipoMovimentacao.SAIDA and dados.quantidade > item.quantidade:
        raise EstoqueInsuficienteError()

    if dados.tipo == TipoMovimentacao.ENTRADA:
        item.quantidade += dados.quantidade
    else:
        item.quantidade -= dados.quantidade

    # Decimal(str(...)) em vez de Decimal(dados.quantidade) evita que a
    # imprecisao binaria do float (ex.: 0.1) vaze para o valor monetario.
    valor_total = Decimal(str(dados.quantidade)) * item.valor_unitario

    movimentacao = Movimentacao(
        item_id=item.id,
        usuario_id=usuario_id,
        tipo=dados.tipo,
        quantidade=dados.quantidade,
        valor_total=valor_total,
    )
    db.add(movimentacao)
    db.commit()
    db.refresh(movimentacao)
    return movimentacao


def _intervalo_mes_atual() -> tuple[date, date]:
    hoje = date.today()
    primeiro_dia = hoje.replace(day=1)
    ultimo_dia_num = calendar.monthrange(hoje.year, hoje.month)[1]
    ultimo_dia = hoje.replace(day=ultimo_dia_num)
    return primeiro_dia, ultimo_dia


def calcular_gastos(
    db: Session,
    usuario_id: uuid.UUID,
    data_inicio: Optional[date],
    data_fim: Optional[date],
) -> tuple[date, date, Decimal, list[Movimentacao]]:
    if data_inicio is None or data_fim is None:
        padrao_inicio, padrao_fim = _intervalo_mes_atual()
        data_inicio = data_inicio or padrao_inicio
        data_fim = data_fim or padrao_fim

    inicio_dt = datetime.combine(data_inicio, time.min)
    fim_dt = datetime.combine(data_fim, time.max)

    movimentacoes = (
        db.query(Movimentacao)
        .filter(
            Movimentacao.usuario_id == usuario_id,
            Movimentacao.tipo == TipoMovimentacao.SAIDA,
            Movimentacao.criado_em >= inicio_dt,
            Movimentacao.criado_em <= fim_dt,
        )
        .order_by(Movimentacao.criado_em)
        .all()
    )

    total_gasto = sum((m.valor_total for m in movimentacoes), Decimal("0"))

    return data_inicio, data_fim, total_gasto, movimentacoes

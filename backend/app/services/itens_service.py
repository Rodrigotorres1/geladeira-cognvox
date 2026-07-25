import uuid

from sqlalchemy.orm import Session

from app.models.item_estoque import ItemEstoque
from app.models.movimentacao import Movimentacao
from app.schemas.itens import ItemAtualizar, ItemCriar


class ItemNaoEncontradoError(Exception):
    pass


class ItemComMovimentacoesError(Exception):
    pass


def listar_itens(db: Session) -> list[ItemEstoque]:
    return db.query(ItemEstoque).order_by(ItemEstoque.nome).all()


def buscar_item(db: Session, item_id: uuid.UUID) -> ItemEstoque:
    item = db.get(ItemEstoque, item_id)
    if item is None:
        raise ItemNaoEncontradoError()
    return item


def criar_item(db: Session, dados: ItemCriar, usuario_id: uuid.UUID) -> ItemEstoque:
    item = ItemEstoque(
        usuario_id=usuario_id,
        nome=dados.nome,
        quantidade=dados.quantidade,
        unidade=dados.unidade,
        valor_unitario=dados.valor_unitario,
        validade=dados.validade,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def atualizar_item(db: Session, item_id: uuid.UUID, dados: ItemAtualizar) -> ItemEstoque:
    item = buscar_item(db, item_id)
    item.nome = dados.nome
    item.quantidade = dados.quantidade
    item.unidade = dados.unidade
    item.valor_unitario = dados.valor_unitario
    item.validade = dados.validade
    db.commit()
    db.refresh(item)
    return item


def remover_item(db: Session, item_id: uuid.UUID) -> None:
    item = buscar_item(db, item_id)

    tem_movimentacoes = (
        db.query(Movimentacao.id).filter(Movimentacao.item_id == item_id).first() is not None
    )
    if tem_movimentacoes:
        raise ItemComMovimentacoesError()

    db.delete(item)
    db.commit()

import uuid
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.lote import Lote
from app.models.tipo_cilindro import TipoCilindro
from app.schemas.tipos import TipoAtualizar, TipoCriar, TipoOut
from app.services import alertas


class TipoNaoEncontradoError(Exception):
    pass


class TipoDuplicadoError(Exception):
    pass


class TipoComLotesError(Exception):
    pass


def montar_tipo_out(tipo: TipoCilindro, hoje: date) -> TipoOut:
    disponivel = alertas.estoque_disponivel(tipo.lotes, hoje)
    return TipoOut(
        id=tipo.id,
        nome=tipo.nome,
        estoque_minimo=tipo.estoque_minimo,
        dias_alerta=tipo.dias_alerta,
        criado_em=tipo.criado_em,
        estoque_disponivel=disponivel,
        estoque_baixo=alertas.estoque_baixo(disponivel, tipo.estoque_minimo),
    )


def listar(db: Session, hoje: Optional[date] = None) -> list[TipoOut]:
    hoje = hoje or alertas.data_hoje()
    tipos = db.query(TipoCilindro).order_by(TipoCilindro.nome).all()
    return [montar_tipo_out(tipo, hoje) for tipo in tipos]


def buscar(db: Session, tipo_id: uuid.UUID) -> TipoCilindro:
    tipo = db.get(TipoCilindro, tipo_id)
    if tipo is None:
        raise TipoNaoEncontradoError()
    return tipo


def _garantir_nome_livre(
    db: Session, nome: str, ignorar_id: Optional[uuid.UUID] = None
) -> None:
    consulta = db.query(TipoCilindro.id).filter(TipoCilindro.nome == nome)
    if ignorar_id is not None:
        consulta = consulta.filter(TipoCilindro.id != ignorar_id)
    if consulta.first() is not None:
        raise TipoDuplicadoError()


def criar(db: Session, dados: TipoCriar) -> TipoOut:
    _garantir_nome_livre(db, dados.nome)
    tipo = TipoCilindro(
        nome=dados.nome,
        estoque_minimo=dados.estoque_minimo,
        dias_alerta=dados.dias_alerta,
    )
    db.add(tipo)
    db.commit()
    db.refresh(tipo)
    return montar_tipo_out(tipo, alertas.data_hoje())


def atualizar(db: Session, tipo_id: uuid.UUID, dados: TipoAtualizar) -> TipoOut:
    tipo = buscar(db, tipo_id)
    _garantir_nome_livre(db, dados.nome, ignorar_id=tipo_id)
    tipo.nome = dados.nome
    tipo.estoque_minimo = dados.estoque_minimo
    tipo.dias_alerta = dados.dias_alerta
    db.commit()
    db.refresh(tipo)
    return montar_tipo_out(tipo, alertas.data_hoje())


def remover(db: Session, tipo_id: uuid.UUID) -> None:
    tipo = buscar(db, tipo_id)

    # Qualquer lote bloqueia, mesmo zerado: todo lote nasce de uma entrada,
    # entao ter lote significa ter historico de movimentacoes.
    tem_lotes = db.query(Lote.id).filter(Lote.tipo_id == tipo_id).first() is not None
    if tem_lotes:
        raise TipoComLotesError()

    db.delete(tipo)
    db.commit()

import uuid
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.lote import Lote
from app.models.tipo_cilindro import TipoCilindro
from app.schemas.tipos import TipoAtualizar, TipoCriar, TipoOut
from app.services import alertas
from app.services.data_teste import calcular_vencimento


class TipoNaoEncontradoError(Exception):
    pass


class TipoDuplicadoError(Exception):
    pass


class TipoComLotesError(Exception):
    pass


def montar_tipo_out(tipo: TipoCilindro, hoje: date) -> TipoOut:
    disponivel = alertas.estoque_disponivel(
        (
            alertas.QuantidadeVencimento(
                lote.quantidade, calcular_vencimento(lote.data_teste, tipo.validade_anos)
            )
            for lote in tipo.lotes
        ),
        hoje,
    )
    return TipoOut(
        id=tipo.id,
        nome=tipo.nome,
        estoque_minimo=tipo.estoque_minimo,
        validade_anos=tipo.validade_anos,
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
    # Compara em Python com casefold() em vez de lower() no SQL: o lower() do
    # SQLite so trata ASCII, entao "ÓXIGÊNIO" e "óxigênio" passariam como
    # nomes diferentes. A tabela de tipos e pequena, ler todos os nomes e ok.
    nome_normalizado = nome.casefold()
    for tipo_id, nome_existente in db.query(TipoCilindro.id, TipoCilindro.nome):
        if tipo_id != ignorar_id and nome_existente.casefold() == nome_normalizado:
            raise TipoDuplicadoError()


def criar(db: Session, dados: TipoCriar) -> TipoOut:
    _garantir_nome_livre(db, dados.nome)
    tipo = TipoCilindro(
        nome=dados.nome,
        estoque_minimo=dados.estoque_minimo,
        validade_anos=dados.validade_anos,
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
    tipo.validade_anos = dados.validade_anos
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

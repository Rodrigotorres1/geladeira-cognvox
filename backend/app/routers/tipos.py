import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.tipos import TipoAtualizar, TipoCriar, TipoOut
from app.services import tipos_service

router = APIRouter(prefix="/tipos", tags=["tipos"], dependencies=[Depends(get_current_user)])


def _tipo_nao_encontrado() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de cilindro não encontrado"
    )


def _tipo_duplicado() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT, detail="Já existe um tipo de cilindro com esse nome"
    )


@router.get("", response_model=list[TipoOut])
def listar_tipos(db: Session = Depends(get_db)):
    return tipos_service.listar(db)


@router.post("", response_model=TipoOut, status_code=status.HTTP_201_CREATED)
def criar_tipo(dados: TipoCriar, db: Session = Depends(get_db)):
    try:
        return tipos_service.criar(db, dados)
    except tipos_service.TipoDuplicadoError:
        raise _tipo_duplicado()


@router.put("/{tipo_id}", response_model=TipoOut)
def atualizar_tipo(tipo_id: uuid.UUID, dados: TipoAtualizar, db: Session = Depends(get_db)):
    try:
        return tipos_service.atualizar(db, tipo_id, dados)
    except tipos_service.TipoNaoEncontradoError:
        raise _tipo_nao_encontrado()
    except tipos_service.TipoDuplicadoError:
        raise _tipo_duplicado()


@router.delete("/{tipo_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_tipo(tipo_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        tipos_service.remover(db, tipo_id)
    except tipos_service.TipoNaoEncontradoError:
        raise _tipo_nao_encontrado()
    except tipos_service.TipoComLotesError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível excluir um tipo que já tem lotes registrados",
        )

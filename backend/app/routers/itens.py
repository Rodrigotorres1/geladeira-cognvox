import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.schemas.itens import ItemAtualizar, ItemCriar, ItemOut
from app.services import itens_service

# dependencies=[Depends(get_current_user)] protege TODAS as rotas deste router:
# sem sessao valida, o FastAPI nem chega a executar a funcao da rota.
router = APIRouter(prefix="/itens", tags=["itens"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[ItemOut])
def listar_itens(db: Session = Depends(get_db)):
    return itens_service.listar_itens(db)


@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def criar_item(
    dados: ItemCriar,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
):
    return itens_service.criar_item(db, dados, usuario_atual.id)


@router.put("/{item_id}", response_model=ItemOut)
def atualizar_item(item_id: uuid.UUID, dados: ItemAtualizar, db: Session = Depends(get_db)):
    try:
        return itens_service.atualizar_item(db, item_id, dados)
    except itens_service.ItemNaoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item nao encontrado"
        )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_item(item_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        itens_service.remover_item(db, item_id)
    except itens_service.ItemNaoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item nao encontrado"
        )

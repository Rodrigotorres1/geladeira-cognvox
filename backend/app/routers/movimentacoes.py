from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.schemas.movimentacoes import MovimentacaoCriar, MovimentacaoOut
from app.services import itens_service, movimentacoes_service

router = APIRouter(
    prefix="/movimentacoes", tags=["movimentacoes"], dependencies=[Depends(get_current_user)]
)


@router.post("", response_model=MovimentacaoOut, status_code=status.HTTP_201_CREATED)
def registrar_movimentacao(
    dados: MovimentacaoCriar,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
):
    try:
        return movimentacoes_service.registrar_movimentacao(db, dados, usuario_atual.id)
    except itens_service.ItemNaoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item nao encontrado"
        )
    except movimentacoes_service.EstoqueInsuficienteError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estoque insuficiente para essa saida",
        )

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.schemas.movimentacoes import EntradaCriar, MovimentacaoOut, SaidaCriar
from app.services import lotes_service, movimentacoes_service, tipos_service

router = APIRouter(
    prefix="/movimentacoes", tags=["movimentacoes"], dependencies=[Depends(get_current_user)]
)


@router.get("", response_model=list[MovimentacaoOut])
def listar_movimentacoes(db: Session = Depends(get_db)):
    return movimentacoes_service.listar(db)


@router.post("/entrada", response_model=MovimentacaoOut, status_code=status.HTTP_201_CREATED)
def registrar_entrada(
    dados: EntradaCriar,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
):
    try:
        return movimentacoes_service.registrar_entrada(db, dados, usuario_atual.id)
    except tipos_service.TipoNaoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de cilindro nao encontrado"
        )


@router.post("/saida", response_model=MovimentacaoOut, status_code=status.HTTP_201_CREATED)
def registrar_saida(
    dados: SaidaCriar,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
):
    try:
        return movimentacoes_service.registrar_saida(db, dados, usuario_atual.id)
    except lotes_service.LoteNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote nao encontrado")
    except movimentacoes_service.EstoqueInsuficienteError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantidade maior que a disponivel no lote",
        )

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.lotes import LoteAtualizar, LoteOut
from app.services import lotes_service

# Sem POST (lote so nasce por entrada) e sem DELETE (lote carrega o historico).
router = APIRouter(prefix="/lotes", tags=["lotes"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[LoteOut])
def listar_lotes(
    tipo_id: Optional[uuid.UUID] = Query(default=None), db: Session = Depends(get_db)
):
    return lotes_service.listar(db, tipo_id=tipo_id)


@router.put("/{lote_id}", response_model=LoteOut)
def atualizar_lote(lote_id: uuid.UUID, dados: LoteAtualizar, db: Session = Depends(get_db)):
    try:
        return lotes_service.atualizar(db, lote_id, dados)
    except lotes_service.LoteNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote não encontrado")
    except lotes_service.LoteDuplicadoError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe outro lote desse tipo com essa data de teste",
        )

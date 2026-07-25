from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.schemas.relatorios import RelatorioGastos
from app.services import movimentacoes_service

router = APIRouter(
    prefix="/relatorios", tags=["relatorios"], dependencies=[Depends(get_current_user)]
)


@router.get("/gastos", response_model=RelatorioGastos)
def relatorio_gastos(
    data_inicio: Optional[date] = Query(default=None),
    data_fim: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
):
    inicio, fim, total_gasto, movimentacoes = movimentacoes_service.calcular_gastos(
        db, usuario_atual.id, data_inicio, data_fim
    )
    return RelatorioGastos(
        usuario_id=usuario_atual.id,
        data_inicio=inicio,
        data_fim=fim,
        total_gasto=total_gasto,
        movimentacoes=movimentacoes,
    )

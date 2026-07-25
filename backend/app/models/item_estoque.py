import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.movimentacao import Movimentacao
    from app.models.usuario import Usuario


class ItemEstoque(Base):
    __tablename__ = "itens_estoque"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    quantidade: Mapped[float] = mapped_column(nullable=False)
    unidade: Mapped[str] = mapped_column(String, nullable=False)
    valor_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    validade: Mapped[Optional[date]] = mapped_column(nullable=True)
    atualizado_em: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )

    usuario: Mapped["Usuario"] = relationship(back_populates="itens_estoque")
    # Sem cascade de delete: movimentacoes sao historico/auditoria de gastos,
    # nao dado descartavel do item. remover_item() em itens_service.py
    # bloqueia a exclusao explicitamente se houver movimentacoes associadas.
    movimentacoes: Mapped[list["Movimentacao"]] = relationship(back_populates="item")

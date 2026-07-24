import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.item_estoque import ItemEstoque
    from app.models.usuario import Usuario


class TipoMovimentacao(str, enum.Enum):
    ENTRADA = "entrada"
    SAIDA = "saida"


class Movimentacao(Base):
    __tablename__ = "movimentacoes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("itens_estoque.id"), nullable=False)
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    tipo: Mapped[TipoMovimentacao] = mapped_column(Enum(TipoMovimentacao), nullable=False)
    quantidade: Mapped[float] = mapped_column(nullable=False)
    valor_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    item: Mapped["ItemEstoque"] = relationship(back_populates="movimentacoes")
    usuario: Mapped["Usuario"] = relationship(back_populates="movimentacoes")

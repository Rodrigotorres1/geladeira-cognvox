import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.lote import Lote
    from app.models.usuario import Usuario


class TipoMovimentacao(str, enum.Enum):
    ENTRADA = "entrada"
    SAIDA = "saida"


class Movimentacao(Base):
    __tablename__ = "movimentacoes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    lote_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lotes.id"), nullable=False)
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    tipo: Mapped[TipoMovimentacao] = mapped_column(Enum(TipoMovimentacao), nullable=False)
    quantidade: Mapped[int] = mapped_column(nullable=False)
    observacao: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    lote: Mapped["Lote"] = relationship(back_populates="movimentacoes")
    usuario: Mapped["Usuario"] = relationship(back_populates="movimentacoes")

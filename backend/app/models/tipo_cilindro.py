import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.lote import Lote


class TipoCilindro(Base):
    __tablename__ = "tipos_cilindro"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    estoque_minimo: Mapped[int] = mapped_column(nullable=False)
    # Validade do teste hidrostatico: vencimento do lote = data_teste + isso.
    validade_anos: Mapped[int] = mapped_column(nullable=False, default=10)
    criado_em: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Sem cascade de delete: remover() em tipos_service.py bloqueia a exclusao
    # de um tipo que tenha qualquer lote, mesmo zerado (o lote carrega o
    # historico de movimentacoes).
    lotes: Mapped[list["Lote"]] = relationship(back_populates="tipo")

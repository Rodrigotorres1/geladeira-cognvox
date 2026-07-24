import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class Sessao(Base):
    __tablename__ = "sessoes"

    # Guarda a sessao do lado do servidor: o cookie so leva o id assinado,
    # nunca dados do usuario. Invalidar a sessao (logout, expiracao) e so
    # apagar/expirar essa linha, sem depender de o cookie "confiar em si mesmo".
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    expira_em: Mapped[datetime] = mapped_column(nullable=False)

    usuario: Mapped["Usuario"] = relationship(back_populates="sessoes")

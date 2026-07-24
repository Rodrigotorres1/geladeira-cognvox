import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.item_estoque import ItemEstoque
    from app.models.movimentacao import Movimentacao


class Usuario(Base):
    __tablename__ = "usuarios"

    # UUID v4 gerado no backend, nunca autoincremento: um ID sequencial (1, 2, 3...)
    # permitiria a qualquer usuário autenticado adivinhar/enumerar IDs de outras pessoas
    # só incrementando o número na URL. Um UUID v4 é aleatório e impossível de adivinhar.
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    itens_estoque: Mapped[list["ItemEstoque"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )
    movimentacoes: Mapped[list["Movimentacao"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )

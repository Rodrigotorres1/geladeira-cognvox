import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.movimentacao import Movimentacao
    from app.models.tipo_cilindro import TipoCilindro


class Lote(Base):
    __tablename__ = "lotes"
    # Um lote e a combinacao tipo + data do teste hidrostatico: uma entrada
    # nova com o mesmo trio soma no lote existente em vez de criar outro (ver
    # registrar_entrada). data_teste_so_ano entra na chave porque "2016" (so
    # ano, gravado como janeiro) e "01/2016" sao informacoes diferentes.
    __table_args__ = (
        UniqueConstraint(
            "tipo_id", "data_teste", "data_teste_so_ano", name="uq_lote_tipo_data_teste"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tipo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tipos_cilindro.id"), nullable=False)
    quantidade: Mapped[int] = mapped_column(nullable=False)
    # Sempre dia 1 do mes. O vencimento nao fica no banco: e data_teste +
    # validade_anos do tipo (ver data_teste.calcular_vencimento).
    data_teste: Mapped[date] = mapped_column(nullable=False)
    data_teste_so_ano: Mapped[bool] = mapped_column(nullable=False, default=False)
    numero_lote: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    tipo: Mapped["TipoCilindro"] = relationship(back_populates="lotes")
    # Sem cascade de delete e sem rota de exclusao: o lote e a ponte entre o
    # tipo e o historico de movimentacoes, entao nunca e apagado — quando
    # zera, so some da listagem principal.
    movimentacoes: Mapped[list["Movimentacao"]] = relationship(back_populates="lote")

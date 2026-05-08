from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.mensagem import Mensagem
from backend.repositories.base import BaseRepository


class MensagemRepository(BaseRepository[Mensagem]):
    def __init__(self, db: Session):
        super().__init__(Mensagem, db)

    def listar_por_conversa(self, conversa_id: str) -> list[Mensagem]:
        stmt = (
            select(Mensagem)
            .where(Mensagem.conversa_id == conversa_id)
            .order_by(Mensagem.criada_em.asc())
        )
        resultado = self.db.execute(stmt)
        return list(resultado.scalars().all())

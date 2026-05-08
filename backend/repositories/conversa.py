from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.models.conversa import Conversa
from backend.repositories.base import BaseRepository


class ConversaRepository(BaseRepository[Conversa]):
    def __init__(self, db: Session):
        super().__init__(Conversa, db)

    def listar_com_mensagens(
        self,
        *,
        usuario_id: int | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Conversa]:
        stmt = select(Conversa).options(selectinload(Conversa.mensagens))
        if usuario_id is not None:
            stmt = stmt.where(Conversa.usuario_id == usuario_id)
        stmt = stmt.order_by(Conversa.criada_em.desc()).offset(skip).limit(limit)
        resultado = self.db.execute(stmt)
        return list(resultado.unique().scalars().all())

    def obter_com_mensagens(self, conversa_id: str) -> Conversa | None:
        stmt = (
            select(Conversa)
            .options(selectinload(Conversa.mensagens))
            .where(Conversa.id == conversa_id)
        )
        resultado = self.db.execute(stmt)
        return resultado.unique().scalar_one_or_none()

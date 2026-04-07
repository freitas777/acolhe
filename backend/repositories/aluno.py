from __future__ import annotations

from sqlalchemy.orm import Session, selectinload

from backend.models.aluno import Aluno
from backend.repositories.base import BaseRepository


class AlunoRepository(BaseRepository[Aluno]):
    def __init__(self, db: Session):
        super().__init__(Aluno, db)

    def list_with_profile(
        self, *, skip: int = 0, limit: int = 100
    ) -> list[Aluno]:
        return (
            self.db.query(Aluno)
            .options(selectinload(Aluno.perfil))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_with_profile(self, id: int) -> Aluno | None:
        return (
            self.db.query(Aluno)
            .options(selectinload(Aluno.perfil))
            .filter(Aluno.id == id)
            .first()
        )

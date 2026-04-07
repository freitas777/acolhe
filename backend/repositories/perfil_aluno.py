from __future__ import annotations

from sqlalchemy.orm import Session

from backend.models.perfil_aluno import PerfilAluno
from backend.repositories.base import BaseRepository


class PerfilAlunoRepository(BaseRepository[PerfilAluno]):
    def __init__(self, db: Session):
        super().__init__(PerfilAluno, db)

    def get_by_aluno_id(self, aluno_id: int) -> PerfilAluno | None:
        return (
            self.db.query(PerfilAluno)
            .filter(PerfilAluno.aluno_id == aluno_id)
            .first()
        )

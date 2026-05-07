from __future__ import annotations

from sqlalchemy.orm import Session

from backend.models.disciplina import Disciplina
from backend.repositories.base import BaseRepository


class DisciplinaRepository(BaseRepository[Disciplina]):
    def __init__(self, db: Session):
        super().__init__(Disciplina, db)

    def listar_por_usuario(self, usuario_id: int, semestre: str | None = None) -> list[Disciplina]:
        query = self.db.query(Disciplina).filter(Disciplina.usuario_id == usuario_id)
        if semestre:
            query = query.filter(Disciplina.semestre == semestre)
        return query.all()

    def deletar_por_usuario_e_semestre(self, usuario_id: int, semestre: str) -> int:
        result = (
            self.db.query(Disciplina)
            .filter(Disciplina.usuario_id == usuario_id, Disciplina.semestre == semestre)
            .delete()
        )
        self.db.commit()
        return result

    def buscar_por_suap_id(self, suap_id: int, usuario_id: int) -> Disciplina | None:
        return (
            self.db.query(Disciplina)
            .filter(Disciplina.suap_id == suap_id, Disciplina.usuario_id == usuario_id)
            .first()
        )

from __future__ import annotations

from sqlalchemy import or_
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

    def get_by_matricula(self, matricula: str) -> Aluno | None:
        return (
            self.db.query(Aluno)
            .filter(Aluno.matricula == matricula)
            .first()
        )

    def get_by_suap_id(self, suap_id: str) -> Aluno | None:
        return (
            self.db.query(Aluno)
            .filter(Aluno.suap_id == suap_id)
            .first()
        )

    def buscar_por_nome_ou_matricula(self, query: str) -> list[Aluno]:
        escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        termo = f"%{escaped}%"
        return (
            self.db.query(Aluno)
            .filter(
                or_(
                    Aluno.nome.ilike(termo),
                    Aluno.matricula.ilike(termo),
                )
            )
            .options(selectinload(Aluno.perfil))
            .limit(50)
            .all()
        )

    def get_all_matriculas(self) -> set[str]:
        results = self.db.query(Aluno.matricula).filter(Aluno.matricula.isnot(None)).all()
        return {r[0] for r in results if r[0]}

    def get_all_suap_ids(self) -> set[str]:
        results = self.db.query(Aluno.suap_id).filter(Aluno.suap_id.isnot(None)).all()
        return {r[0] for r in results if r[0]}

    def get_matricula_lookup(self) -> dict[str, Aluno]:
        rows = (
            self.db.query(Aluno)
            .filter(Aluno.matricula.isnot(None))
            .all()
        )
        return {a.matricula: a for a in rows if a.matricula}

    def listar_por_status(self, status_acompanhamento: str) -> list[Aluno]:
        return (
            self.db.query(Aluno)
            .filter(Aluno.status_acompanhamento == status_acompanhamento)
            .options(selectinload(Aluno.perfil))
            .all()
        )

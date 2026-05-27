from __future__ import annotations

from sqlalchemy.orm import Session, selectinload

from backend.models.aluno import Aluno
from backend.models.conteudo_gerado import ConteudoGerado
from backend.models.perfil_aluno import PerfilAluno
from backend.schemas.portal import PerfilAlunoSelfUpdate


class PortalService:
    def __init__(self, db: Session):
        self.db = db

    def obter_meu_perfil(self, suap_id: str) -> Aluno | None:
        return (
            self.db.query(Aluno)
            .options(selectinload(Aluno.perfil))
            .filter(Aluno.suap_id == suap_id)
            .first()
        )

    def atualizar_meu_perfil(
        self, suap_id: str, data: PerfilAlunoSelfUpdate
    ) -> PerfilAluno:
        aluno = (
            self.db.query(Aluno)
            .options(selectinload(Aluno.perfil))
            .filter(Aluno.suap_id == suap_id)
            .first()
        )
        if not aluno:
            raise ValueError("Aluno nao encontrado para o suap_id informado")

        perfil = aluno.perfil
        if not perfil:
            perfil = PerfilAluno(aluno_id=aluno.id)
            self.db.add(perfil)
            self.db.flush()

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(perfil, key, value)

        self.db.commit()
        self.db.refresh(perfil)
        return perfil

    def listar_meus_conteudos(self, suap_id: str) -> list[ConteudoGerado]:
        aluno = (
            self.db.query(Aluno)
            .filter(Aluno.suap_id == suap_id)
            .first()
        )
        if not aluno:
            return []

        return (
            self.db.query(ConteudoGerado)
            .filter(ConteudoGerado.aluno_id == aluno.id)
            .order_by(ConteudoGerado.gerado_em.desc())
            .all()
        )

    def obter_conteudo(self, suap_id: str, conteudo_id: int) -> ConteudoGerado | None:
        aluno = (
            self.db.query(Aluno)
            .filter(Aluno.suap_id == suap_id)
            .first()
        )
        if not aluno:
            return None

        conteudo = (
            self.db.query(ConteudoGerado)
            .filter(
                ConteudoGerado.id == conteudo_id,
                ConteudoGerado.aluno_id == aluno.id,
            )
            .first()
        )
        return conteudo

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.models.usuario import Usuario
from backend.models.disciplina import Disciplina
from backend.repositories.usuario import UsuarioRepository
from backend.repositories.disciplina import DisciplinaRepository
from backend.services.suap_service import SUAPService
from backend.schemas.auth import UsuarioSUAPResponse, DisciplinaResponse
from backend.database import get_db
from fastapi import Depends, HTTPException, status


class AuthService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.usuario_repo = UsuarioRepository(db)
        self.disciplina_repo = DisciplinaRepository(db)
        self.suap_service = SUAPService()

    async def login_com_suap(self, token: str, semestre: str = "2026.1") -> dict:
        meus_dados = await self.suap_service.get_meus_dados(token)

        suap_id = str(meus_dados.get("id", ""))
        nome = meus_dados.get("nome_usual", "")
        email = meus_dados.get("email", "")
        matricula = meus_dados.get("matricula", "")
        tipo_vinculo = meus_dados.get("tipo_vinculo", "")
        campus = ""
        if meus_dados.get("vinculo"):
            campus = meus_dados["vinculo"].get("campus", "")

        tipo_perfil = "aluno"
        if tipo_vinculo and tipo_vinculo.lower() not in ("aluno", "estudante"):
            tipo_perfil = "professor"

        usuario = self.usuario_repo.get_by_suap_id(suap_id)
        if usuario:
            update_data = {
                "nome": nome,
                "email": email,
                "matricula": matricula,
                "tipo_vinculo": tipo_vinculo,
                "campus": campus,
                "tipo_perfil": tipo_perfil,
            }
            for key, value in update_data.items():
                setattr(usuario, key, value)
            self.db.commit()
            self.db.refresh(usuario)
        else:
            usuario_data = {
                "suap_id": suap_id,
                "nome": nome,
                "email": email,
                "matricula": matricula,
                "tipo_vinculo": tipo_vinculo,
                "campus": campus,
                "tipo_perfil": tipo_perfil,
            }
            usuario = self.usuario_repo.create(usuario_data)

        try:
            disciplinas_raw = await self.suap_service.get_disciplinas(token, semestre)
            self._sincronizar_disciplinas(usuario.id, disciplinas_raw, semestre)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Falha ao sincronizar disciplinas para usuario {usuario.id}: {e}")

        self.db.refresh(usuario)

        return {
            "usuario": UsuarioSUAPResponse.model_validate(usuario),
            "disciplinas": [
                DisciplinaResponse.model_validate(d)
                for d in self.disciplina_repo.listar_por_usuario(usuario.id, semestre)
            ],
        }

    def _sincronizar_disciplinas(self, usuario_id: int, disciplinas_raw: list[dict], semestre: str):
        self.disciplina_repo.deletar_por_usuario_e_semestre(usuario_id, semestre)

        for disc_raw in disciplinas_raw:
            disciplina_data = {
                "suap_id": disc_raw.get("id", 0),
                "descricao": disc_raw.get("descricao", ""),
                "sigla": disc_raw.get("sigla", ""),
                "situacao": disc_raw.get("situacao", {}).get("rotulo", "") if isinstance(disc_raw.get("situacao"), dict) else str(disc_raw.get("situacao", "")),
                "professor": disc_raw.get("docente", "") or disc_raw.get("professor", ""),
                "semestre": semestre,
                "usuario_id": usuario_id,
            }
            self.disciplina_repo.create(disciplina_data)

    def obter_usuario_atual(self, usuario_id: int) -> Usuario:
        usuario = self.usuario_repo.get_by_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado",
            )
        return usuario

    def obter_disciplinas(self, usuario_id: int, semestre: str | None = None) -> list[Disciplina]:
        return self.disciplina_repo.listar_por_usuario(usuario_id, semestre)

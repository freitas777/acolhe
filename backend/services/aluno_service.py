from __future__ import annotations

from typing import List

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.repositories.aluno import AlunoRepository
from backend.services.perfil_aluno_service import PerfilAlunoService
from backend.schemas.aluno import AlunoCreate, AlunoResponse, AlunoUpdate
from backend.schemas.perfil_aluno import PerfilAlunoCreate, PerfilAlunoResponse, PerfilAlunoUpdate


class AlunoService: 
    def __init__(self, db: Session = Depends(get_db)):
        self.aluno_repository = AlunoRepository(db)
        self.perfil_service = PerfilAlunoService(db)

    def criar_aluno(self, aluno_data: AlunoCreate) -> AlunoResponse:
        aluno = self.aluno_repository.create(aluno_data.model_dump())
        return AlunoResponse.model_validate(aluno)

    def listar_alunos(self, skip: int = 0, limit: int = 100) -> List[AlunoResponse]:
        alunos = self.aluno_repository.list_with_profile(skip=skip, limit=limit)
        return [AlunoResponse.model_validate(aluno) for aluno in alunos]

    def obter_aluno_por_id(self, aluno_id: int) -> AlunoResponse:
        aluno = self.aluno_repository.get_with_profile(aluno_id)
        if not aluno:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aluno não encontrado"
            )
        return AlunoResponse.model_validate(aluno)

    def atualizar_aluno(self, aluno_id: int, aluno_data: AlunoUpdate) -> AlunoResponse:
        aluno = self.aluno_repository.get_by_id(aluno_id)
        if not aluno:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aluno não encontrado"
            )

        update_data = aluno_data.model_dump(exclude_unset=True)
        aluno_atualizado = self.aluno_repository.update(aluno_id, update_data)
        
        return AlunoResponse.model_validate(aluno_atualizado)

    def deletar_aluno(self, aluno_id: int) -> None:
        aluno = self.aluno_repository.get_by_id(aluno_id)
        if not aluno:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aluno não encontrado"
            )
        self.aluno_repository.delete(aluno_id)

    def criar_perfil(self, aluno_id: int, perfil_data: PerfilAlunoCreate) -> PerfilAlunoResponse:
        return self.perfil_service.criar_perfil(aluno_id, perfil_data)

    def obter_perfil(self, aluno_id: int) -> PerfilAlunoResponse:
        return self.perfil_service.obter_perfil_por_aluno(aluno_id)

    def atualizar_perfil(self, aluno_id: int, perfil_data: PerfilAlunoUpdate) -> PerfilAlunoResponse:
        return self.perfil_service.atualizar_perfil(aluno_id, perfil_data)

# backend/services/perfil_aluno_service.py
from __future__ import annotations

from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.repositories.perfil_aluno import PerfilAlunoRepository
from backend.repositories.aluno import AlunoRepository
from backend.schemas.perfil_aluno import PerfilAlunoCreate, PerfilAlunoResponse, PerfilAlunoUpdate

class PerfilAlunoService:
    def __init__(self, db: Session = Depends(get_db)):
        self.perfil_repository = PerfilAlunoRepository(db)
        self.aluno_repository = AlunoRepository(db)

    def criar_perfil(self, aluno_id: int, perfil_data: PerfilAlunoCreate) -> PerfilAlunoResponse:
        if not self.aluno_repository.get_by_id(aluno_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aluno não encontrado"
            )

        existing_perfil = self.perfil_repository.get_by_aluno_id(aluno_id)
        if existing_perfil:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Perfil já existe para este aluno. Utilize PUT para atualizar."
            )

        perfil_dict = perfil_data.model_dump()
        perfil_dict["aluno_id"] = aluno_id
        
        novo_perfil = self.perfil_repository.create(perfil_dict)
        return PerfilAlunoResponse.model_validate(novo_perfil)

    def obter_perfil_por_aluno(self, aluno_id: int) -> PerfilAlunoResponse:
        perfil = self.perfil_repository.get_by_aluno_id(aluno_id)
        if not perfil:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil não encontrado para este aluno"
            )
        return PerfilAlunoResponse.model_validate(perfil)

    def atualizar_perfil(self, aluno_id: int, perfil_data: PerfilAlunoUpdate) -> PerfilAlunoResponse:
        perfil = self.perfil_repository.get_by_aluno_id(aluno_id)
        if not perfil:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil não encontrado para atualizar"
            )

        update_data = perfil_data.model_dump(exclude_unset=True)
        perfil_atualizado = self.perfil_repository.update(perfil.id, update_data)
        
        return PerfilAlunoResponse.model_validate(perfil_atualizado)

    def deletar_perfil(self, aluno_id: int) -> None:
        perfil = self.perfil_repository.get_by_aluno_id(aluno_id)
        if not perfil:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil não encontrado"
            )
        
        sucesso = self.perfil_repository.delete(perfil.id)
        if not sucesso:
             raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao deletar perfil"
            )

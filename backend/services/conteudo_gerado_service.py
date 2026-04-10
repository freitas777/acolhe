from __future__ import annotations

from typing import List, Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.repositories.aluno import AlunoRepository
from backend.repositories.usuario import UsuarioRepository
from backend.repositories.conteudo_gerado import ConteudoGeradoRepository
from backend.schemas.conteudo_gerado import (
    ConteudoGeradoCreate,
    ConteudoGeradoResponse,
    ConteudoGeradoUpdate
)


class ConteudoGeradoService:
    def __init__(self, db: Session = Depends(get_db)):
        self.conteudo_repository = ConteudoGeradoRepository(db)
        self.aluno_repository = AlunoRepository(db)
        self.usuario_repository = UsuarioRepository(db)

    def criar_conteudo(self, conteudo_data: ConteudoGeradoCreate) -> ConteudoGeradoResponse:
        if not self.aluno_repository.get_by_id(conteudo_data.aluno_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aluno não encontrado"
            )
        if conteudo_data.usuario_id is not None:
            if not self.usuario_repository.get_by_id(conteudo_data.usuario_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuário responsável não encontrado"
                )

        # 3. Salva o conteúdo
        conteudo = self.conteudo_repository.create(conteudo_data.model_dump())
        return ConteudoGeradoResponse.model_validate(conteudo)

    def listar_conteudos(
        self, aluno_id: Optional[int] = None, skip: int = 0, limit: int = 100
    ) -> List[ConteudoGeradoResponse]:
        
        if aluno_id:
            # Valida se o aluno existe antes de filtrar
            if not self.aluno_repository.get_by_id(aluno_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Aluno não encontrado"
                )
            conteudos = self.conteudo_repository.list_by_aluno(aluno_id)
        else:
            conteudos = self.conteudo_repository.list_all(skip=skip, limit=limit)

        return [ConteudoGeradoResponse.model_validate(c) for c in conteudos]

    def obter_conteudo_por_id(self, conteudo_id: int) -> ConteudoGeradoResponse:
        conteudo = self.conteudo_repository.get_by_id(conteudo_id)
        if not conteudo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conteúdo não encontrado"
            )
        return ConteudoGeradoResponse.model_validate(conteudo)

    def atualizar_conteudo(
        self, conteudo_id: int, conteudo_data: ConteudoGeradoUpdate
    ) -> ConteudoGeradoResponse:
        conteudo = self.conteudo_repository.get_by_id(conteudo_id)
        if not conteudo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conteúdo não encontrado"
            )

        update_data = conteudo_data.model_dump(exclude_unset=True)
        conteudo_atualizado = self.conteudo_repository.update(conteudo_id, update_data)
        
        return ConteudoGeradoResponse.model_validate(conteudo_atualizado)

    def deletar_conteudo(self, conteudo_id: int) -> None:
        conteudo = self.conteudo_repository.get_by_id(conteudo_id)
        if not conteudo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conteúdo não encontrado"
            )
        self.conteudo_repository.delete(conteudo_id)

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from backend.models.usuario import TipoPerfil
from backend.repositories.usuario import UsuarioRepository
from backend.schemas.usuario import UsuarioCreate, UsuarioResponse, UsuarioUpdate
from backend.database import get_db
from fastapi import Depends, HTTPException, status


class UsuarioService:
    def __init__(self, db: Session = Depends(get_db)):
        self.repository = UsuarioRepository(db)

    def criar_usuario(self, usuario_data: UsuarioCreate) -> UsuarioResponse:
        existing_usuario = self.repository.get_by_suap_id(usuario_data.suap_id)
        if existing_usuario:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe um usuário com este SUAP ID"
            )

        usuario = self.repository.create(usuario_data.model_dump())
        return UsuarioResponse.model_validate(usuario)

    def listar_usuarios(self, skip: int = 0, limit: int = 100) -> List[UsuarioResponse]:
        usuarios = self.repository.list_all(skip=skip, limit=limit)
        return [UsuarioResponse.model_validate(usuario) for usuario in usuarios]

    def obter_usuario_por_id(self, usuario_id: int) -> UsuarioResponse:
        usuario = self.repository.get_by_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        return UsuarioResponse.model_validate(usuario)

    def atualizar_usuario(self, usuario_id: int, usuario_data: UsuarioUpdate) -> UsuarioResponse:
        usuario = self.repository.get_by_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )

        update_data = usuario_data.model_dump(exclude_unset=True)
        usuario_atualizado = self.repository.update(usuario_id, update_data)

        if not usuario_atualizado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )

        return UsuarioResponse.model_validate(usuario_atualizado)

    def deletar_usuario(self, usuario_id: int) -> None:
        usuario = self.repository.get_by_id(usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )

        sucesso = self.repository.delete(usuario_id)
        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao deletar usuário"
            )

    def obter_usuarios_por_perfil(self, perfil: TipoPerfil) -> List[UsuarioResponse]:
        usuarios = self.repository.filter_by_profile(perfil)
        return [UsuarioResponse.model_validate(usuario) for usuario in usuarios]
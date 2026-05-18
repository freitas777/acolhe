from __future__ import annotations

import logging

import httpx
from fastapi import Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.usuario import Usuario
from backend.repositories.usuario import UsuarioRepository
from backend.services.suap_service import SUAPService

logger = logging.getLogger(__name__)


class AuthData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    usuario: Usuario
    suap_token: str


async def get_current_usuario(
    request: Request,
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
) -> AuthData:
    cached = getattr(request.state, "_auth_data", None)
    if cached is not None:
        return cached

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autorização não fornecido.",
        )

    suap_token = authorization[7:]
    if not suap_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autorização não fornecido.",
        )

    suap_service = SUAPService()
    try:
        meus_dados = await suap_service.get_meus_dados(suap_token)
    except httpx.HTTPStatusError as e:
        if e.response.status_code in (401, 403):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido ou expirado. Faça login novamente.",
            )
        logger.warning(f"Erro HTTP SUAP ao validar token: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="SUAP indisponível. Tente novamente em alguns segundos.",
        )
    except Exception as e:
        logger.warning(f"Erro de conexão ao validar token SUAP: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="SUAP indisponível. Tente novamente em alguns segundos.",
        )

    suap_id = str(meus_dados.get("id", ""))
    if not suap_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não foi possível identificar o usuário no SUAP.",
        )

    usuario_repo = UsuarioRepository(db)
    usuario = usuario_repo.get_by_suap_id(suap_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado no sistema local. Faça login novamente.",
        )

    try:
        eu_dados = await suap_service.get_eu(suap_token)
        novo_campus = eu_dados.get("campus", "")
        if novo_campus and novo_campus != (usuario.campus or ""):
            usuario.campus = novo_campus
            db.commit()
            db.refresh(usuario)
            logger.info(f"Campus atualizado para usuario {usuario.id}: {novo_campus}")
    except Exception as e:
        logger.warning(f"Nao foi possivel atualizar campus do usuario {usuario.id}: {e}")

    auth_data = AuthData(usuario=usuario, suap_token=suap_token)
    request.state._auth_data = auth_data
    return auth_data


def require_napne(auth_data: AuthData = Depends(get_current_usuario)) -> AuthData:
    if auth_data.usuario.tipo_perfil not in ("psicopedagogo", "servidor", "admin", "aluno"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a membros do NAPNE ou servidores autorizados.",
        )
    return auth_data

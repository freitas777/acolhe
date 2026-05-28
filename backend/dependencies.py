from __future__ import annotations

import logging
import time

import httpx
from fastapi import Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.usuario import Usuario
from backend.models.conta_local import ContaLocal
from backend.repositories.usuario import UsuarioRepository
from backend.security import is_jwt_local, validar_jwt
from backend.services.suap_service import SUAPService

logger = logging.getLogger(__name__)

_AUTH_CACHE: dict[str, tuple[float, str]] = {}
_AUTH_CACHE_TTL = 300


class AuthData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    usuario: Usuario
    suap_token: str = ""


async def _authenticate_local(token: str, db: Session) -> AuthData | None:
    if not is_jwt_local(token):
        return None
    payload = validar_jwt(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token local invalido ou expirado. Faca login novamente.",
        )
    usuario_id = payload.get("usuario_id")
    if not usuario_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token local malformado.",
        )
    usuario_repo = UsuarioRepository(db)
    usuario = usuario_repo.get_by_id(usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token local invalido ou expirado. Faca login novamente.",
        )
    conta = db.query(ContaLocal).filter(ContaLocal.usuario_id == usuario.id).first()
    if not conta or not conta.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada.",
        )
    return AuthData(usuario=usuario, suap_token="")


async def _authenticate_suap(suap_token: str, db: Session) -> AuthData:
    now = time.time()
    cached_entry = _AUTH_CACHE.get(suap_token)
    if cached_entry and (now - cached_entry[0]) < _AUTH_CACHE_TTL:
        usuario_repo_cache = UsuarioRepository(db)
        usuario = usuario_repo_cache.get_by_suap_id(cached_entry[1])
        if usuario:
            return AuthData(usuario=usuario, suap_token=suap_token)

    suap_service = SUAPService()
    try:
        meus_dados = await suap_service.get_meus_dados(suap_token)
    except httpx.HTTPStatusError as e:
        if e.response.status_code in (401, 403):
            _AUTH_CACHE.pop(suap_token, None)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalido ou expirado. Faca login novamente.",
            )
        logger.warning(f"Erro HTTP SUAP ao validar token: {e}")
        if cached_entry:
            usuario_repo_fallback = UsuarioRepository(db)
            usuario = usuario_repo_fallback.get_by_suap_id(cached_entry[1])
            if usuario:
                return AuthData(usuario=usuario, suap_token=suap_token)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="SUAP indisponivel. Tente novamente em alguns segundos.",
        )
    except Exception as e:
        logger.warning(f"Erro de conexao ao validar token SUAP: {e}")
        if cached_entry:
            usuario_repo_fallback = UsuarioRepository(db)
            usuario = usuario_repo_fallback.get_by_suap_id(cached_entry[1])
            if usuario:
                return AuthData(usuario=usuario, suap_token=suap_token)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="SUAP indisponivel. Tente novamente em alguns segundos.",
        )

    suap_id = str(meus_dados.get("id", ""))
    if not suap_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nao foi possivel identificar o usuario no SUAP.",
        )

    usuario_repo = UsuarioRepository(db)
    usuario = usuario_repo.get_by_suap_id(suap_id)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario nao encontrado no sistema local. Faca login novamente.",
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

    _AUTH_CACHE[suap_token] = (now, suap_id)
    return AuthData(usuario=usuario, suap_token=suap_token)


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
            detail="Token de autorizacao nao fornecido.",
        )

    token = authorization[7:]
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autorizacao nao fornecido.",
        )

    if is_jwt_local(token):
        auth_data = await _authenticate_local(token, db)
    else:
        auth_data = await _authenticate_suap(token, db)

    request.state._auth_data = auth_data
    return auth_data


def require_napne(auth_data: AuthData = Depends(get_current_usuario)) -> AuthData:
 if auth_data.usuario.tipo_perfil not in ("psicopedagogo", "servidor", "admin"):
  raise HTTPException(
   status_code=status.HTTP_403_FORBIDDEN,
   detail="Acesso restrito a membros do NAPNE ou servidores autorizados.",
  )
 return auth_data


def require_psicopedagogo_or_admin(auth_data: AuthData = Depends(get_current_usuario)) -> AuthData:
 if auth_data.usuario.tipo_perfil not in ("psicopedagogo", "admin"):
  raise HTTPException(
   status_code=status.HTTP_403_FORBIDDEN,
   detail="Acesso restrito a psicopedagogos ou administradores.",
  )
 return auth_data


def require_admin(auth_data: AuthData = Depends(get_current_usuario)) -> AuthData:
 if auth_data.usuario.tipo_perfil != "admin":
  raise HTTPException(
   status_code=status.HTTP_403_FORBIDDEN,
   detail="Acesso restrito a administradores.",
  )
 return auth_data

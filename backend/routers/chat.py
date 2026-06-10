from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import AuthData, get_current_usuario, require_napne
from backend.schemas.chat import (
    ChatRequisicao,
    ChatResposta,
    ConversaCriar,
    ConversaResposta,
    ConteudoEducacionalRequisicao,
    ConteudoEducacionalResposta,
)
from backend.services.chat_service import ChatService

router = APIRouter(prefix="/api/chat", tags=["Chat"])


def _service(db: Session = Depends(get_db)) -> ChatService:
    return ChatService(db)


@router.post(
    "/conversations",
    response_model=ConversaResposta,
    response_model_by_alias=False,
    status_code=status.HTTP_201_CREATED,
)
async def criar_conversa(
 dados: ConversaCriar,
 auth_data: AuthData = Depends(get_current_usuario),
 service: ChatService = Depends(_service),
):
    return await service.criar_conversa(dados, usuario_id=auth_data.usuario.id)


@router.get(
    "/conversations",
    response_model=list[ConversaResposta],
    response_model_by_alias=False,
)
async def listar_conversas(
 auth_data: AuthData = Depends(get_current_usuario),
 service: ChatService = Depends(_service),
):
    return service.listar_conversas(
        usuario_id=auth_data.usuario.id,
        tipo_perfil=auth_data.usuario.tipo_perfil,
    )


@router.post("/send", response_model=ChatResposta, response_model_by_alias=False)
async def enviar_mensagem(
 dados: ChatRequisicao,
 auth_data: AuthData = Depends(get_current_usuario),
 service: ChatService = Depends(_service),
):
    return await service.enviar_mensagem(
        dados,
        usuario_id=auth_data.usuario.id,
        tipo_perfil=auth_data.usuario.tipo_perfil,
    )


@router.post(
    "/educational-content",
    response_model=ConteudoEducacionalResposta,
    response_model_by_alias=False,
)
async def gerar_conteudo_educacional(
 dados: ConteudoEducacionalRequisicao,
 auth_data: AuthData = Depends(require_napne),
 service: ChatService = Depends(_service),
):
    return await service.gerar_conteudo_educacional(dados)


@router.delete(
    "/conversations/{conversa_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def deletar_conversa(
    conversa_id: str,
    auth_data: AuthData = Depends(get_current_usuario),
    service: ChatService = Depends(_service),
):
    await service.deletar_conversa(
        conversa_id,
        usuario_id=auth_data.usuario.id,
        tipo_perfil=auth_data.usuario.tipo_perfil,
    )
    return None

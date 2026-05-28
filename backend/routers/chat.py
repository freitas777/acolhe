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
    status_code=status.HTTP_201_CREATED,
)
async def criar_conversa(
 dados: ConversaCriar,
 auth_data: AuthData = Depends(get_current_usuario),
 service: ChatService = Depends(_service),
):
 return service.criar_conversa(dados, usuario_id=auth_data.usuario.id)


@router.get(
    "/conversations",
    response_model=list[ConversaResposta],
)
async def listar_conversas(
 auth_data: AuthData = Depends(get_current_usuario),
 service: ChatService = Depends(_service),
):
 return service.listar_conversas(usuario_id=auth_data.usuario.id)


@router.post("/send", response_model=ChatResposta)
async def enviar_mensagem(
 dados: ChatRequisicao,
 auth_data: AuthData = Depends(get_current_usuario),
 service: ChatService = Depends(_service),
):
 return await service.enviar_mensagem(dados, usuario_id=auth_data.usuario.id)


@router.post(
    "/educational-content",
    response_model=ConteudoEducacionalResposta,
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
 conversa = service.conversa_repo.get_by_id(conversa_id)
 if not conversa:
  raise HTTPException(status_code=404, detail="Conversa nao encontrada")
 if conversa.usuario_id and conversa.usuario_id != auth_data.usuario.id:
  if auth_data.usuario.tipo_perfil not in ("psicopedagogo", "admin"):
   raise HTTPException(status_code=403, detail="Voce nao pode deletar esta conversa.")
 service.deletar_conversa(conversa_id)

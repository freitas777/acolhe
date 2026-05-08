from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
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
    service: ChatService = Depends(_service),
):
    return service.criar_conversa(dados)


@router.get(
    "/conversations",
    response_model=list[ConversaResposta],
)
async def listar_conversas(
    service: ChatService = Depends(_service),
):
    return service.listar_conversas()


@router.post("/send", response_model=ChatResposta)
async def enviar_mensagem(
    dados: ChatRequisicao,
    service: ChatService = Depends(_service),
):
    return await service.enviar_mensagem(dados)


@router.post(
    "/educational-content",
    response_model=ConteudoEducacionalResposta,
)
async def gerar_conteudo_educacional(
    dados: ConteudoEducacionalRequisicao,
    service: ChatService = Depends(_service),
):
    return await service.gerar_conteudo_educacional(dados)


@router.delete(
    "/conversations/{conversa_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def deletar_conversa(
    conversa_id: str,
    service: ChatService = Depends(_service),
):
    service.deletar_conversa(conversa_id)

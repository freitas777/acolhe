from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.models.conversa import Conversa
from backend.models.mensagem import Mensagem
from backend.repositories.conversa import ConversaRepository
from backend.repositories.mensagem import MensagemRepository
from backend.schemas.chat import (
    ChatRequisicao,
    ChatResposta,
    ConversaCriar,
    ConversaResposta,
    ConteudoEducacionalRequisicao,
    ConteudoEducacionalResposta,
    MensagemResposta,
)
from backend.services.ai_service import ai_service

logger = logging.getLogger(__name__)


def _para_mensagem_resposta(msg: Mensagem) -> MensagemResposta:
    return MensagemResposta(
        id=msg.id,
        role="user" if msg.papel == "usuario" else "assistant",
        content=msg.conteudo,
        created_at=msg.criada_em,
    )


def _para_conversa_resposta(conversa: Conversa) -> ConversaResposta:
    return ConversaResposta(
        id=conversa.id,
        title=conversa.titulo,
        messages=[_para_mensagem_resposta(m) for m in conversa.mensagens],
        created_at=conversa.criada_em,
        user_id=conversa.usuario_id,
    )


class ChatService:
    def __init__(self, db: Session):
        self.conversa_repo = ConversaRepository(db)
        self.mensagem_repo = MensagemRepository(db)
        self.db = db

    def criar_conversa(
        self,
        dados: ConversaCriar,
        usuario_id: int | None = None,
    ) -> ConversaResposta:
        conversa = self.conversa_repo.create({
            "id": str(uuid.uuid4()),
            "titulo": dados.titulo,
            "usuario_id": usuario_id,
        })

        ai_service.iniciar_sessao(conversa.id)

        logger.info("Conversa criada: id=%s", conversa.id)
        return _para_conversa_resposta(conversa)

    def listar_conversas(
        self,
        usuario_id: int | None = None,
    ) -> list[ConversaResposta]:
        conversas = self.conversa_repo.listar_com_mensagens(
            usuario_id=usuario_id,
        )
        return [_para_conversa_resposta(c) for c in conversas]

    def obter_conversa(self, conversa_id: str) -> ConversaResposta:
        conversa = self.conversa_repo.obter_com_mensagens(conversa_id)
        if not conversa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversa não encontrada",
            )
        return _para_conversa_resposta(conversa)

    async def enviar_mensagem(
        self,
        dados: ChatRequisicao,
        usuario_id: int | None = None,
    ) -> ChatResposta:
        conversa_id = dados.conversation_id

        if conversa_id:
            conversa = self.conversa_repo.obter_com_mensagens(conversa_id)
            if not conversa:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversa não encontrada",
                )
        else:
            titulo = dados.message[:50] + ("..." if len(dados.message) > 50 else "")
            conversa = self.conversa_repo.create({
                "id": str(uuid.uuid4()),
                "titulo": titulo,
                "usuario_id": usuario_id,
            })
            conversa_id = conversa.id
            ai_service.iniciar_sessao(conversa_id)

        msg_usuario = self.mensagem_repo.create({
            "id": str(uuid.uuid4()),
            "conversa_id": conversa_id,
            "papel": "usuario",
            "conteudo": dados.message,
        })

        if len(conversa.mensagens) == 0 and conversa.titulo == "Nova conversa":
            self.conversa_repo.update(conversa_id, {
                "titulo": dados.message[:50] + ("..." if len(dados.message) > 50 else ""),
            })

        logger.info("Mensagem recebida: conversa=%s", conversa_id)

        try:
            conteudo_ia = await ai_service.gerar_resposta(
                conversa_id=conversa_id,
                mensagem_usuario=dados.message,
            )
            msg_assistente = self.mensagem_repo.create({
                "id": str(uuid.uuid4()),
                "conversa_id": conversa_id,
                "papel": "assistente",
                "conteudo": conteudo_ia,
            })
            resposta_assistente = _para_mensagem_resposta(msg_assistente)
        except Exception as exc:
            logger.error("Erro na IA: %s", exc)
            msg_assistente = self.mensagem_repo.create({
                "id": str(uuid.uuid4()),
                "conversa_id": conversa_id,
                "papel": "assistente",
                "conteudo": "Desculpe, estou com dificuldades para responder no momento. Tente novamente.",
            })
            resposta_assistente = _para_mensagem_resposta(msg_assistente)

        return ChatResposta(
            user_message=_para_mensagem_resposta(msg_usuario),
            assistant_message=resposta_assistente,
            conversation_id=conversa_id,
        )

    def deletar_conversa(self, conversa_id: str) -> bool:
        conversa = self.conversa_repo.get_by_id(conversa_id)
        if not conversa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversa não encontrada",
            )
        resultado = self.conversa_repo.delete(conversa_id)
        ai_service.encerrar_sessao(conversa_id)
        logger.info("Conversa deletada: id=%s", conversa_id)
        return resultado

    async def gerar_conteudo_educacional(
        self,
        dados: ConteudoEducacionalRequisicao,
    ) -> ConteudoEducacionalResposta:
        conteudo = await ai_service.gerar_conteudo_educacional(
            tema=dados.tema,
            perfil_aluno=dados.perfil_aluno,
        )
        return ConteudoEducacionalResposta(
            success=True,
            tema=dados.tema,
            conteudo=conteudo,
            gerado_em=datetime.now(timezone.utc).isoformat(),
        )

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.models.conversa import Conversa
from backend.models.mensagem import Mensagem
from backend.repositories.aluno import AlunoRepository
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
    aluno_nome = None
    if conversa.aluno:
        aluno_nome = conversa.aluno.nome

    return ConversaResposta(
        id=conversa.id,
        title=conversa.titulo,
        messages=[_para_mensagem_resposta(m) for m in conversa.mensagens],
        created_at=conversa.criada_em,
        user_id=conversa.usuario_id,
        aluno_id=conversa.aluno_id,
        aluno_nome=aluno_nome,
    )


class ChatService:
    def __init__(self, db: Session):
        self.conversa_repo = ConversaRepository(db)
        self.mensagem_repo = MensagemRepository(db)
        self.aluno_repo = AlunoRepository(db)
        self.db = db

    def _obter_contexto_aluno(self, aluno_id: int) -> Optional[str]:
        aluno = self.aluno_repo.get_with_profile(aluno_id)
        if not aluno:
            return None
        perfil = aluno.perfil if hasattr(aluno, "perfil") else None
        if not perfil:
            return None
        return ai_service.construir_contexto_aluno(aluno, perfil)

    async def _criar_conversa_com_contexto(
        self,
        titulo: str,
        usuario_id: int,
        aluno_id: int | None = None,
    ) -> Conversa:
        contexto_aluno = None
        if aluno_id:
            contexto_aluno = self._obter_contexto_aluno(aluno_id)
            if contexto_aluno is None:
                logger.warning("Aluno id=%s sem perfil — conversa criada sem contexto de aluno", aluno_id)

        conversa = self.conversa_repo.create({
            "id": str(uuid.uuid4()),
            "titulo": titulo,
            "usuario_id": usuario_id,
            "aluno_id": aluno_id,
        })

        await ai_service.iniciar_sessao(conversa.id, contexto_aluno=contexto_aluno)
        return conversa

    async def criar_conversa(
        self,
        dados: ConversaCriar,
        usuario_id: int,
    ) -> ConversaResposta:
        conversa = await self._criar_conversa_com_contexto(
            titulo=dados.titulo,
            usuario_id=usuario_id,
            aluno_id=dados.aluno_id,
        )

        logger.info("Conversa criada: id=%s, aluno_id=%s", conversa.id, dados.aluno_id)
        return _para_conversa_resposta(conversa)

    def _verificar_propriedade(
        self, conversa: Conversa, usuario_id: int, tipo_perfil: str,
    ) -> None:
        if conversa.usuario_id != usuario_id:
            if tipo_perfil not in ("psicopedagogo", "admin"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Você não tem permissão para acessar esta conversa.",
                )

    def listar_conversas(
        self,
        usuario_id: int,
        tipo_perfil: str = "aluno",
    ) -> list[ConversaResposta]:
        if tipo_perfil in ("psicopedagogo", "admin"):
            conversas = self.conversa_repo.listar_com_mensagens()
        else:
            conversas = self.conversa_repo.listar_com_mensagens(
                usuario_id=usuario_id,
            )
        return [_para_conversa_resposta(c) for c in conversas]

    def obter_conversa(
        self,
        conversa_id: str,
        usuario_id: int,
        tipo_perfil: str = "aluno",
    ) -> ConversaResposta:
        conversa = self.conversa_repo.obter_com_mensagens(conversa_id)
        if not conversa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversa não encontrada",
            )
        self._verificar_propriedade(conversa, usuario_id, tipo_perfil)
        return _para_conversa_resposta(conversa)

    async def enviar_mensagem(
        self,
        dados: ChatRequisicao,
        usuario_id: int | None = None,
        tipo_perfil: str = "aluno",
    ) -> ChatResposta:
        conversa_id = dados.conversation_id
        aluno_id = dados.aluno_id

        if conversa_id:
            conversa = self.conversa_repo.obter_com_mensagens(conversa_id)
            if not conversa:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversa não encontrada",
                )

            if usuario_id is not None:
                self._verificar_propriedade(conversa, usuario_id, tipo_perfil)

            if aluno_id and conversa.aluno_id != aluno_id:
                contexto_aluno = self._obter_contexto_aluno(aluno_id)
                if contexto_aluno:
                    self.conversa_repo.update(conversa_id, {"aluno_id": aluno_id})
                    await ai_service.encerrar_sessao(conversa_id)
                    await ai_service.iniciar_sessao(conversa_id, contexto_aluno=contexto_aluno)
                    conversa = self.conversa_repo.obter_com_mensagens(conversa_id)
                else:
                    logger.warning("Aluno id=%s sem perfil — contexto de aluno não aplicado", aluno_id)

            if not aluno_id and conversa.aluno_id:
                contexto_aluno = self._obter_contexto_aluno(conversa.aluno_id)
                if contexto_aluno:
                    await ai_service.garantir_sessao_com_contexto(conversa_id, contexto_aluno=contexto_aluno)
        else:
            titulo = dados.message[:50] + ("..." if len(dados.message) > 50 else "")
            conversa = await self._criar_conversa_com_contexto(
                titulo=titulo,
                usuario_id=usuario_id,
                aluno_id=aluno_id,
            )
            conversa_id = conversa.id

        msg_usuario = self.mensagem_repo.create({
            "id": str(uuid.uuid4()),
            "conversa_id": conversa_id,
            "papel": "usuario",
            "conteudo": dados.message,
        })

        conversa = self.conversa_repo.obter_com_mensagens(conversa_id)
        if len(conversa.mensagens) == 1 and conversa.titulo == "Nova conversa":
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

        conversa_atualizada = self.conversa_repo.obter_com_mensagens(conversa_id)
        aluno_nome = None
        if conversa_atualizada and conversa_atualizada.aluno:
            aluno_nome = conversa_atualizada.aluno.nome

        return ChatResposta(
            user_message=_para_mensagem_resposta(msg_usuario),
            assistant_message=resposta_assistente,
            conversation_id=conversa_id,
            aluno_id=conversa_atualizada.aluno_id if conversa_atualizada else None,
            aluno_nome=aluno_nome,
        )

    async def deletar_conversa(
        self,
        conversa_id: str,
        usuario_id: int | None = None,
        tipo_perfil: str = "aluno",
    ) -> bool:
        conversa = self.conversa_repo.get_by_id(conversa_id)
        if not conversa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversa não encontrada",
            )
        if usuario_id is not None:
            self._verificar_propriedade(conversa, usuario_id, tipo_perfil)
        resultado = self.conversa_repo.delete(conversa_id)
        await ai_service.encerrar_sessao(conversa_id)
        logger.info("Conversa deletada: id=%s", conversa_id)
        return resultado

    async def gerar_conteudo_educacional(
        self,
        dados: ConteudoEducacionalRequisicao,
    ) -> ConteudoEducacionalResposta:
        conteudo = await ai_service.gerar_conteudo_educacional(
            tema=dados.tema,
            perfil_aluno=dados.perfil_aluno.model_dump(),
        )
        return ConteudoEducacionalResposta(
            success=True,
            tema=dados.tema,
            conteudo=conteudo,
            gerado_em=datetime.now(timezone.utc).isoformat(),
        )

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models.conversa import Conversa
from backend.models.mensagem import Mensagem
from backend.repositories.acomodacao_observacao import AcomodacaoObservacaoRepository
from backend.repositories.aluno import AlunoRepository
from backend.repositories.conversa import ConversaRepository
from backend.repositories.disciplina import DisciplinaRepository
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
from backend.services.prompt_builder import prompt_builder

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

    disciplina_descricao = None
    disciplina_sigla = None
    if conversa.disciplina:
        disciplina_descricao = conversa.disciplina.descricao
        disciplina_sigla = conversa.disciplina.sigla

    return ConversaResposta(
        id=conversa.id,
        title=conversa.titulo,
        messages=[_para_mensagem_resposta(m) for m in conversa.mensagens],
        created_at=conversa.criada_em,
        updated_at=conversa.atualizada_em,
        user_id=conversa.usuario_id,
        aluno_id=conversa.aluno_id,
        aluno_nome=aluno_nome,
        disciplina_id=conversa.disciplina_id,
        disciplina_descricao=disciplina_descricao,
        disciplina_sigla=disciplina_sigla,
    )


class ChatService:
    def __init__(self, db: Session):
        self.conversa_repo = ConversaRepository(db)
        self.mensagem_repo = MensagemRepository(db)
        self.aluno_repo = AlunoRepository(db)
        self.disciplina_repo = DisciplinaRepository(db)
        self.acomodacao_repo = AcomodacaoObservacaoRepository(db)
        self.db = db

    def _construir_system_instruction(
        self,
        aluno_id: int | None = None,
        disciplina_id: int | None = None,
        mensagens: list[Mensagem] | None = None,
    ) -> str:
        aluno = None
        perfil = None
        if aluno_id:
            aluno = self.aluno_repo.get_with_profile(aluno_id)
            if aluno:
                perfil = getattr(aluno, "perfil", None)

        disciplina = None
        if disciplina_id:
            disciplina = self.disciplina_repo.get_by_id(disciplina_id)

        observacoes = []
        if aluno_id:
            observacoes = self.acomodacao_repo.listar_por_aluno(aluno_id)

        return prompt_builder.build_session_instruction(
            aluno=aluno,
            perfil=perfil,
            disciplina=disciplina,
            observacoes=observacoes,
            mensagens=mensagens,
        )

    async def _criar_conversa_com_contexto(
        self,
        titulo: str,
        usuario_id: int,
        aluno_id: int | None = None,
        disciplina_id: int | None = None,
    ) -> Conversa:
        if aluno_id:
            aluno = self.aluno_repo.get_with_profile(aluno_id)
            if not aluno or not getattr(aluno, "perfil", None):
                logger.warning("Aluno id=%s sem perfil → conversa criada sem contexto de aluno", aluno_id)

        if disciplina_id:
            disciplina = self.disciplina_repo.get_by_id(disciplina_id)
            if not disciplina:
                logger.warning("Disciplina id=%s não encontrada → conversa criada sem contexto de disciplina", disciplina_id)

        conversa = self.conversa_repo.create({
            "id": str(uuid.uuid4()),
            "titulo": titulo,
            "usuario_id": usuario_id,
            "aluno_id": aluno_id,
            "disciplina_id": disciplina_id,
        })

        system_instruction = self._construir_system_instruction(
            aluno_id=aluno_id,
            disciplina_id=disciplina_id,
        )

        await ai_service.iniciar_sessao(
            conversa.id,
            system_instruction=system_instruction,
        )
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
            disciplina_id=dados.disciplina_id,
        )

        logger.info(
            "Conversa criada: id=%s, aluno_id=%s, disciplina_id=%s",
            conversa.id, dados.aluno_id, dados.disciplina_id,
        )
        return _para_conversa_resposta(conversa)

    async def obter_ou_criar_conversa_disciplina(
        self,
        disciplina_id: int,
        usuario_id: int,
        tipo_perfil: str = "aluno",
        suap_id: str | None = None,
    ) -> ConversaResposta:
        conversa_existente = self.conversa_repo.obter_por_usuario_e_disciplina(
            usuario_id, disciplina_id,
        )

        if conversa_existente:
            self._verificar_propriedade(conversa_existente, usuario_id, tipo_perfil)
            mensagens_existentes = self.mensagem_repo.listar_por_conversa(conversa_existente.id)
            system_instruction = self._construir_system_instruction(
                aluno_id=conversa_existente.aluno_id,
                disciplina_id=disciplina_id,
                mensagens=mensagens_existentes,
            )
            await ai_service.garantir_sessao_com_contexto(
                conversa_id=conversa_existente.id,
                system_instruction=system_instruction,
                mensagens=mensagens_existentes,
            )
            return _para_conversa_resposta(conversa_existente)

        disciplina = self.disciplina_repo.get_by_id(disciplina_id)
        if not disciplina:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Disciplina nÃ£o encontrada",
            )

        titulo = f"Conversa sobre {disciplina.descricao}"

        aluno_id = None
        if tipo_perfil == "aluno" and suap_id:
            aluno = self.aluno_repo.get_by_suap_id(suap_id)
            if aluno:
                aluno_id = aluno.id
                if not getattr(aluno, "perfil", None):
                    logger.warning("Aluno id=%s sem perfil â conversa criada sem contexto de aluno", aluno.id)

        conversa = self.conversa_repo.create({
            "id": str(uuid.uuid4()),
            "titulo": titulo,
            "usuario_id": usuario_id,
            "aluno_id": aluno_id,
            "disciplina_id": disciplina_id,
        })

        system_instruction = self._construir_system_instruction(
            aluno_id=aluno_id,
            disciplina_id=disciplina_id,
        )

        await ai_service.iniciar_sessao(
            conversa.id,
            system_instruction=system_instruction,
        )

        logger.info(
            "Conversa de disciplina criada: id=%s, disciplina_id=%s, aluno_id=%s",
            conversa.id, disciplina_id, aluno_id,
        )
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

    async def _preparar_envio(
        self,
        dados: ChatRequisicao,
        usuario_id: int | None = None,
        tipo_perfil: str = "aluno",
    ) -> tuple[str, Mensagem]:
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
                system_instruction = self._construir_system_instruction(
                    aluno_id=aluno_id,
                    disciplina_id=conversa.disciplina_id,
                )
                if system_instruction:
                    self.conversa_repo.update(conversa_id, {"aluno_id": aluno_id})
                    await ai_service.encerrar_sessao(conversa_id)
                    await ai_service.iniciar_sessao(conversa_id, system_instruction=system_instruction)
                    conversa = self.conversa_repo.obter_com_mensagens(conversa_id)
                else:
                    logger.warning("Aluno id=%s sem perfil → contexto de aluno não aplicado", aluno_id)

            if not aluno_id and conversa.aluno_id:
                mensagens_existentes = self.mensagem_repo.listar_por_conversa(conversa_id)
                system_instruction = self._construir_system_instruction(
                    aluno_id=conversa.aluno_id,
                    disciplina_id=conversa.disciplina_id,
                    mensagens=mensagens_existentes,
                )
                await ai_service.garantir_sessao_com_contexto(
                    conversa_id, system_instruction=system_instruction, mensagens=mensagens_existentes,
                )
        else:
            titulo = dados.message[:50] + ("..." if len(dados.message) > 50 else "")
            conversa = await self._criar_conversa_com_contexto(
                titulo=titulo,
                usuario_id=usuario_id,
                aluno_id=aluno_id,
                disciplina_id=dados.disciplina_id,
            )
            conversa_id = conversa.id

        msg_usuario = self.mensagem_repo.create({
            "id": str(uuid.uuid4()),
            "conversa_id": conversa_id,
            "papel": "usuario",
            "conteudo": dados.message,
        })

        conversa = self.conversa_repo.obter_com_mensagens(conversa_id)
        update_data = {"atualizada_em": datetime.now(timezone.utc)}
        if len(conversa.mensagens) == 1 and conversa.titulo == "Nova conversa":
            update_data["titulo"] = dados.message[:50] + ("..." if len(dados.message) > 50 else "")
        self.conversa_repo.update(conversa_id, update_data)

        logger.info("Mensagem recebida: conversa=%s", conversa_id)
        return conversa_id, msg_usuario

    async def enviar_mensagem(
        self,
        dados: ChatRequisicao,
        usuario_id: int | None = None,
        tipo_perfil: str = "aluno",
    ) -> ChatResposta:
        conversa_id, msg_usuario = await self._preparar_envio(dados, usuario_id, tipo_perfil)

        try:
            mensagens_db = self.mensagem_repo.listar_por_conversa(conversa_id)
            conteudo_ia = await ai_service.gerar_resposta(
                conversa_id=conversa_id,
                mensagem_usuario=dados.message,
                mensagens=mensagens_db,
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

        disciplina_descricao = None
        if conversa_atualizada and conversa_atualizada.disciplina:
            disciplina_descricao = conversa_atualizada.disciplina.descricao

        return ChatResposta(
            user_message=_para_mensagem_resposta(msg_usuario),
            assistant_message=resposta_assistente,
            conversation_id=conversa_id,
            aluno_id=conversa_atualizada.aluno_id if conversa_atualizada else None,
            aluno_nome=aluno_nome,
            disciplina_id=conversa_atualizada.disciplina_id if conversa_atualizada else None,
            disciplina_descricao=disciplina_descricao,
        )

    async def enviar_mensagem_stream(
        self,
        dados: ChatRequisicao,
        usuario_id: int | None = None,
        tipo_perfil: str = "aluno",
    ):
        conversa_id, msg_usuario = await self._preparar_envio(dados, usuario_id, tipo_perfil)

        user_msg_data = _para_mensagem_resposta(msg_usuario)
        yield f"data: {json.dumps({'type': 'user_message', 'message': user_msg_data.model_dump(mode='json')})}\n\n"
        yield f"data: {json.dumps({'type': 'conversation_id', 'conversation_id': conversa_id})}\n\n"

        conversa = self.conversa_repo.obter_com_mensagens(conversa_id)
        aluno_id = conversa.aluno_id if conversa else None
        aluno_nome = conversa.aluno.nome if conversa and conversa.aluno else None
        disciplina_id = conversa.disciplina_id if conversa else None
        disciplina_descricao = conversa.disciplina.descricao if conversa and conversa.disciplina else None
        yield f"data: {json.dumps({'type': 'meta', 'aluno_id': aluno_id, 'aluno_nome': aluno_nome, 'disciplina_id': disciplina_id, 'disciplina_descricao': disciplina_descricao})}\n\n"

        conteudo_completo = []
        try:
            mensagens_db = self.mensagem_repo.listar_por_conversa(conversa_id)
            async for chunk in ai_service.gerar_resposta_stream(
                conversa_id=conversa_id,
                mensagem_usuario=dados.message,
                mensagens=mensagens_db,
            ):
                conteudo_completo.append(chunk)
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
        except Exception as exc:
            logger.error("Erro no streaming da IA: %s", exc)
            if not conteudo_completo:
                fallback = "Desculpe, estou com dificuldades para responder no momento. Tente novamente."
                yield f"data: {json.dumps({'type': 'error', 'content': fallback})}\n\n"
                conteudo_completo.append(fallback)
            else:
                yield f"data: {json.dumps({'type': 'error', 'content': ' [resposta interrompida]'})}\n\n"

        texto_completo = "".join(conteudo_completo)
        db = SessionLocal()
        try:
            msg_assistente = Mensagem(
                id=str(uuid.uuid4()),
                conversa_id=conversa_id,
                papel="assistente",
                conteudo=texto_completo,
            )
            db.add(msg_assistente)
            conversa_db = db.query(Conversa).filter(Conversa.id == conversa_id).first()
            if conversa_db:
                conversa_db.atualizada_em = datetime.now(timezone.utc)
            db.commit()
            db.refresh(msg_assistente)
            assistant_msg_data = MensagemResposta(
                id=msg_assistente.id,
                role="assistant",
                content=msg_assistente.conteudo,
                created_at=msg_assistente.criada_em,
            )
            yield f"data: {json.dumps({'type': 'done', 'message': assistant_msg_data.model_dump(mode='json')})}\n\n"
        except Exception as exc:
            logger.error("Erro ao salvar mensagem assistente: %s", exc)
            yield f"data: {json.dumps({'type': 'done', 'message': None})}\n\n"
        finally:
            db.close()

    async def vincular_aluno(
        self,
        conversa_id: str,
        aluno_id: int,
        usuario_id: int,
        tipo_perfil: str = "aluno",
    ) -> ConversaResposta:
        conversa = self.conversa_repo.obter_com_mensagens(conversa_id)
        if not conversa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversa nao encontrada",
            )
        self._verificar_propriedade(conversa, usuario_id, tipo_perfil)

        aluno = self.aluno_repo.get_with_profile(aluno_id)
        if not aluno:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aluno nao encontrado",
            )

        self.conversa_repo.update(conversa_id, {"aluno_id": aluno_id})

        mensagens_existentes = self.mensagem_repo.listar_por_conversa(conversa_id)
        system_instruction = self._construir_system_instruction(
            aluno_id=aluno_id,
            disciplina_id=conversa.disciplina_id,
            mensagens=mensagens_existentes,
        )
        await ai_service.encerrar_sessao(conversa_id)
        await ai_service.iniciar_sessao(
            conversa_id,
            system_instruction=system_instruction,
        )

        conversa_atualizada = self.conversa_repo.obter_com_mensagens(conversa_id)
        logger.info("Aluno id=%s vinculado a conversa id=%s", aluno_id, conversa_id)
        return _para_conversa_resposta(conversa_atualizada)

    async def desvincular_aluno(
        self,
        conversa_id: str,
        usuario_id: int,
        tipo_perfil: str = "aluno",
    ) -> ConversaResposta:
        conversa = self.conversa_repo.obter_com_mensagens(conversa_id)
        if not conversa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversa nao encontrada",
            )
        self._verificar_propriedade(conversa, usuario_id, tipo_perfil)

        self.conversa_repo.update(conversa_id, {"aluno_id": None})

        mensagens_existentes = self.mensagem_repo.listar_por_conversa(conversa_id)
        system_instruction = self._construir_system_instruction(
            aluno_id=None,
            disciplina_id=conversa.disciplina_id,
            mensagens=mensagens_existentes,
        )
        await ai_service.encerrar_sessao(conversa_id)
        await ai_service.iniciar_sessao(
            conversa_id,
            system_instruction=system_instruction,
        )

        conversa_atualizada = self.conversa_repo.obter_com_mensagens(conversa_id)
        logger.info("Aluno desvinculado da conversa id=%s", conversa_id)
        return _para_conversa_resposta(conversa_atualizada)

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

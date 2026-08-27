from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session, selectinload

from backend.models.conteudo_feedback import ConteudoFeedback


class ConteudoFeedbackRepository:
    """Repository para feedback de conteúdos gerados por IA."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def listar_por_conteudo(self, conteudo_id: int) -> list[ConteudoFeedback]:
        """Lista todos os feedbacks de um conteúdo."""
        return (
            self.db.query(ConteudoFeedback)
            .options(
                selectinload(ConteudoFeedback.professor),
                selectinload(ConteudoFeedback.disciplina),
            )
            .filter(ConteudoFeedback.conteudo_id == conteudo_id)
            .all()
        )

    def listar_por_professor(self, professor_id: int) -> list[ConteudoFeedback]:
        """Lista todos os feedbacks de um professor."""
        return (
            self.db.query(ConteudoFeedback)
            .options(
                selectinload(ConteudoFeedback.conteudo),
                selectinload(ConteudoFeedback.disciplina),
            )
            .filter(ConteudoFeedback.professor_id == professor_id)
            .all()
        )

    def get_por_conteudo_professor_disciplina(
        self, conteudo_id: int, professor_id: int, disciplina_id: Optional[int] = None
    ) -> Optional[ConteudoFeedback]:
        """Obtém feedback específico de um professor para um conteúdo."""
        query = self.db.query(ConteudoFeedback).filter(
            ConteudoFeedback.conteudo_id == conteudo_id,
            ConteudoFeedback.professor_id == professor_id,
        )
        if disciplina_id:
            query = query.filter(ConteudoFeedback.disciplina_id == disciplina_id)
        return query.first()

    def criar_ou_atualizar(
        self,
        conteudo_id: int,
        professor_id: int,
        avaliacao: str,
        utilidade_percebida: Optional[int] = None,
        disciplina_id: Optional[int] = None,
        comentario: Optional[str] = None,
    ) -> ConteudoFeedback:
        """Cria ou atualiza feedback (upsert)."""
        feedback = self.get_por_conteudo_professor_disciplina(
            conteudo_id, professor_id, disciplina_id
        )

        if feedback:
            # Atualizar existente
            feedback.avaliacao = avaliacao
            feedback.utilidade_percebida = utilidade_percebida
            feedback.comentario = comentario
            self.db.flush()
        else:
            # Criar novo
            feedback = ConteudoFeedback(
                conteudo_id=conteudo_id,
                professor_id=professor_id,
                disciplina_id=disciplina_id,
                avaliacao=avaliacao,
                utilidade_percebida=utilidade_percebida,
                comentario=comentario,
            )
            self.db.add(feedback)
            self.db.flush()

        self.db.refresh(feedback)
        return feedback
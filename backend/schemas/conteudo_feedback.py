from __future__ import annotations

from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, ConfigDict

# Literal para avaliação (sem criar Enum no banco)
AvaliacaoLiteral = Literal["util", "parcial", "nao_util"]


class ConteudoFeedbackCreate(BaseModel):
    """Schema para criação de feedback."""

    disciplina_id: Optional[int] = None
    avaliacao: AvaliacaoLiteral
    utilidade_percebida: Optional[int] = None
    comentario: Optional[str] = None


class ConteudoFeedbackResponse(BaseModel):
    """Schema para resposta de feedback."""

    id: int
    conteudo_id: int
    professor_id: Optional[int]
    professor_nome: Optional[str]
    disciplina_id: int
    disciplina_sigla: Optional[str]
    avaliacao: str
    utilidade_percebida: Optional[int]
    comentario: Optional[str]
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)
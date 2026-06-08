from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, Field


class ConversaCriar(BaseModel):
    titulo: str = Field(default="Nova conversa", max_length=255)
    aluno_id: Optional[int] = None


class ConversaResposta(BaseModel):
    id: str
    title: str = Field(alias="titulo")
    messages: list["MensagemResposta"] = []
    created_at: datetime = Field(alias="criada_em")
    user_id: Optional[int] = Field(None, alias="usuario_id")
    aluno_id: Optional[int] = None
    aluno_nome: Optional[str] = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class MensagemResposta(BaseModel):
    id: str
    role: str = Field(alias="papel")
    content: str = Field(alias="conteudo")
    created_at: datetime = Field(alias="criada_em")

    model_config = {"from_attributes": True, "populate_by_name": True}


class ChatRequisicao(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[str] = None
    aluno_id: Optional[int] = None


class ChatResposta(BaseModel):
    user_message: MensagemResposta
    assistant_message: Optional[MensagemResposta] = None
    conversation_id: str
    aluno_id: Optional[int] = None
    aluno_nome: Optional[str] = None


class PerfilAlunoDict(BaseModel):
    nivel_atencao: Optional[str] = None
    dificuldade_leitura: Optional[bool] = None
    preferencia: Optional[str] = None
    interesses: Optional[str] = None
    diagnostico: Optional[str] = None


class ConteudoEducacionalRequisicao(BaseModel):
    tema: str = Field(..., min_length=1, max_length=300)
    perfil_aluno: PerfilAlunoDict


class ConteudoEducacionalResposta(BaseModel):
    success: bool
    tema: str
    conteudo: str
    gerado_em: str

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ConversaCriar(BaseModel):
    titulo: str = Field(default="Nova conversa", max_length=255)


class ConversaResposta(BaseModel):
    id: str
    title: str
    messages: list["MensagemResposta"] = []
    created_at: datetime
    user_id: Optional[int] = None

    model_config = {"from_attributes": True}


class MensagemResposta(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatRequisicao(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[str] = None


class ChatResposta(BaseModel):
    user_message: MensagemResposta
    assistant_message: Optional[MensagemResposta] = None
    conversation_id: str


class ConteudoEducacionalRequisicao(BaseModel):
    tema: str = Field(..., min_length=1, max_length=300)
    perfil_aluno: dict


class ConteudoEducacionalResposta(BaseModel):
    success: bool
    tema: str
    conteudo: str
    gerado_em: str

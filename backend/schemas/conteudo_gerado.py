from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ConteudoGeradoCreate(BaseModel):
    aluno_id: int
    usuario_id: Optional[int] = None
    tema: str
    prompt_utilizado: str
    conteudo: str
    modelo_ia: str


class ConteudoGeradoUpdate(BaseModel):
    tema: Optional[str] = None
    prompt_utilizado: Optional[str] = None
    conteudo: Optional[str] = None
    modelo_ia: Optional[str] = None


class ConteudoGeradoResponse(BaseModel):
    id: int
    aluno_id: int
    usuario_id: Optional[int] = None
    tema: str
    prompt_utilizado: str
    conteudo: str
    modelo_ia: str
    gerado_em: datetime

    model_config = {"from_attributes": True}

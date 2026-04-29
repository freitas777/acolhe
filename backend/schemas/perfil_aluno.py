from typing import Optional
from pydantic import BaseModel
from backend.models.perfil_aluno import NivelAtencao, PreferenciaAprendizado


class PerfilAlunoCreate(BaseModel):
    nivel_atencao: Optional[NivelAtencao] = None
    dificuldade_leitura: bool = False
    preferencia: Optional[PreferenciaAprendizado] = None
    interesses: Optional[str] = None
    diagnostico: Optional[str] = None


class PerfilAlunoUpdate(BaseModel):
    nivel_atencao: Optional[NivelAtencao] = None
    dificuldade_leitura: Optional[bool] = None
    preferencia: Optional[PreferenciaAprendizado] = None
    interesses: Optional[str] = None
    diagnostico: Optional[str] = None


class PerfilAlunoResponse(BaseModel):
    id: int
    aluno_id: int  
    nivel_atencao: Optional[NivelAtencao] = None
    dificuldade_leitura: bool
    preferencia: Optional[PreferenciaAprendizado] = None
    interesses: Optional[str] = None
    diagnostico: Optional[str] = None

    model_config = {"from_attributes": True}

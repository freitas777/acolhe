from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.aluno_service import AlunoService
from backend.schemas.aluno import AlunoCreate, AlunoResponse, AlunoUpdate
from backend.schemas.perfil_aluno import PerfilAlunoCreate, PerfilAlunoResponse, PerfilAlunoUpdate

router = APIRouter(prefix="/alunos", tags=["Alunos"])


def _service(db: Session) -> AlunoService:
    return AlunoService(db)


@router.post(
    "/",
    response_model=AlunoResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_aluno(data: AlunoCreate, db: Session = Depends(get_db)):
    service = _service(db)
    return service.criar_aluno(data)


@router.get("/", response_model=list[AlunoResponse])
def list_alunos(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    service = _service(db)
    return service.listar_alunos(skip=skip, limit=limit)


@router.get("/{aluno_id}", response_model=AlunoResponse)
def get_aluno(aluno_id: int, db: Session = Depends(get_db)):
    service = _service(db)
    return service.obter_aluno_por_id(aluno_id)


@router.put("/{aluno_id}", response_model=AlunoResponse)
def update_aluno(
    aluno_id: int, data: AlunoUpdate, db: Session = Depends(get_db)
):
    service = _service(db)
    return service.atualizar_aluno(aluno_id, data)


@router.delete("/{aluno_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_aluno(aluno_id: int, db: Session = Depends(get_db)):
    service = _service(db)
    service.deletar_aluno(aluno_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Nested Perfil endpoints ---


@router.post(
    "/{aluno_id}/perfil",
    response_model=PerfilAlunoResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_perfil(
    aluno_id: int, data: PerfilAlunoCreate, db: Session = Depends(get_db)
):
    service = _service(db)
    return service.criar_perfil(aluno_id, data)


@router.get(
    "/{aluno_id}/perfil", response_model=PerfilAlunoResponse
)
def get_perfil(aluno_id: int, db: Session = Depends(get_db)):
    service = _service(db)
    return service.obter_perfil(aluno_id)


@router.put(
    "/{aluno_id}/perfil", response_model=PerfilAlunoResponse
)
def update_perfil(
    aluno_id: int, data: PerfilAlunoUpdate, db: Session = Depends(get_db)
):
    service = _service(db)
    return service.atualizar_perfil(aluno_id, data)

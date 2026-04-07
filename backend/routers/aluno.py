from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.repositories.aluno import AlunoRepository
from backend.repositories.perfil_aluno import PerfilAlunoRepository
from backend.schemas.aluno import AlunoCreate, AlunoResponse, AlunoUpdate
from backend.schemas.perfil_aluno import PerfilAlunoCreate, PerfilAlunoResponse

router = APIRouter(prefix="/alunos", tags=["Alunos"])


def _aluno_repo(db: Session) -> AlunoRepository:
    return AlunoRepository(db)


def _perfil_repo(db: Session) -> PerfilAlunoRepository:
    return PerfilAlunoRepository(db)


@router.post(
    "/",
    response_model=AlunoResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_aluno(data: AlunoCreate, db: Session = Depends(get_db)):
    aluno = _aluno_repo(db).create(data.model_dump())
    return aluno


@router.get("/", response_model=list[AlunoResponse])
def list_alunos(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    return _aluno_repo(db).list_with_profile(skip=skip, limit=limit)


@router.get("/{aluno_id}", response_model=AlunoResponse)
def get_aluno(aluno_id: int, db: Session = Depends(get_db)):
    aluno = _aluno_repo(db).get_with_profile(aluno_id)
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno nao encontrado")
    return aluno


@router.put("/{aluno_id}", response_model=AlunoResponse)
def update_aluno(
    aluno_id: int, data: AlunoUpdate, db: Session = Depends(get_db)
):
    payload = data.model_dump(exclude_none=True)
    updated = _aluno_repo(db).update(aluno_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Aluno nao encontrado")
    return updated


@router.delete("/{aluno_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_aluno(aluno_id: int, db: Session = Depends(get_db)):
    deleted = _aluno_repo(db).delete(aluno_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Aluno nao encontrado")
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
    aluno = _aluno_repo(db).get_by_id(aluno_id)
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno nao encontrado")

    existing = _perfil_repo(db).get_by_aluno_id(aluno_id)
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Perfil ja existe para este aluno, use PUT para atualizar",
        )

    perfil_data = data.model_dump()
    perfil_data["aluno_id"] = aluno_id
    return _perfil_repo(db).create(perfil_data)


@router.get(
    "/{aluno_id}/perfil", response_model=PerfilAlunoResponse
)
def get_perfil(aluno_id: int, db: Session = Depends(get_db)):
    perfil = _perfil_repo(db).get_by_aluno_id(aluno_id)
    if not perfil:
        raise HTTPException(
            status_code=404, detail="Perfil nao encontrado para este aluno"
        )
    return perfil


@router.put(
    "/{aluno_id}/perfil", response_model=PerfilAlunoResponse
)
def update_perfil(
    aluno_id: int, data: PerfilAlunoCreate, db: Session = Depends(get_db)
):
    perfil = _perfil_repo(db).get_by_aluno_id(aluno_id)
    if not perfil:
        raise HTTPException(
            status_code=404, detail="Perfil nao encontrado para este aluno"
        )
    payload = data.model_dump(exclude_none=True)
    updated = _perfil_repo(db).update(perfil.id, payload)
    return updated

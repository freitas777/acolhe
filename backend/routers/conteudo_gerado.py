from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.repositories.aluno import AlunoRepository
from backend.repositories.conteudo_gerado import ConteudoGeradoRepository
from backend.schemas.conteudo_gerado import (
    ConteudoGeradoCreate,
    ConteudoGeradoResponse,
    ConteudoGeradoUpdate,
)

router = APIRouter(prefix="/conteudos", tags=["Conteudos Gerados"])


def _conteudo_repo(db: Session) -> ConteudoGeradoRepository:
    return ConteudoGeradoRepository(db)


def _aluno_repo(db: Session) -> AlunoRepository:
    return AlunoRepository(db)


@router.post(
    "/",
    response_model=ConteudoGeradoResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_conteudo(data: ConteudoGeradoCreate, db: Session = Depends(get_db)):
    aluno = _aluno_repo(db).get_by_id(data.aluno_id)
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno nao encontrado")

    conteudo = _conteudo_repo(db).create(data.model_dump())
    return conteudo


@router.get("/", response_model=list[ConteudoGeradoResponse])
def list_conteudos(
    aluno_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    if aluno_id:
        return _conteudo_repo(db).list_by_aluno(aluno_id)
    return _conteudo_repo(db).list_all(skip=skip, limit=limit)


@router.get("/{conteudo_id}", response_model=ConteudoGeradoResponse)
def get_conteudo(conteudo_id: int, db: Session = Depends(get_db)):
    conteudo = _conteudo_repo(db).get_by_id(conteudo_id)
    if not conteudo:
        raise HTTPException(
            status_code=404, detail="Conteudo nao encontrado"
        )
    return conteudo


@router.put("/{conteudo_id}", response_model=ConteudoGeradoResponse)
def update_conteudo(
    conteudo_id: int, data: ConteudoGeradoUpdate, db: Session = Depends(get_db)
):
    payload = data.model_dump(exclude_none=True)
    updated = _conteudo_repo(db).update(conteudo_id, payload)
    if not updated:
        raise HTTPException(
            status_code=404, detail="Conteudo nao encontrado"
        )
    return updated


@router.delete(
    "/{conteudo_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_conteudo(conteudo_id: int, db: Session = Depends(get_db)):
    deleted = _conteudo_repo(db).delete(conteudo_id)
    if not deleted:
        raise HTTPException(
            status_code=404, detail="Conteudo nao encontrado"
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

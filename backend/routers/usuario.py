from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.repositories.usuario import UsuarioRepository
from backend.schemas.usuario import UsuarioCreate, UsuarioResponse, UsuarioUpdate

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


def _repo(db: Session) -> UsuarioRepository:
    return UsuarioRepository(db)


@router.post(
    "/",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_usuario(data: UsuarioCreate, db: Session = Depends(get_db)):
    usuario = _repo(db).create(data.model_dump())
    return usuario


@router.get("/", response_model=list[UsuarioResponse])
def list_usuarios(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    return _repo(db).list_all(skip=skip, limit=limit)


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def get_usuario(usuario_id: int, db: Session = Depends(get_db)):
    usuario = _repo(db).get_by_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    return usuario


@router.put("/{usuario_id}", response_model=UsuarioResponse)
def update_usuario(
    usuario_id: int, data: UsuarioUpdate, db: Session = Depends(get_db)
):
    payload = data.model_dump(exclude_none=True)
    updated = _repo(db).update(usuario_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    return updated


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_usuario(usuario_id: int, db: Session = Depends(get_db)):
    deleted = _repo(db).delete(usuario_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

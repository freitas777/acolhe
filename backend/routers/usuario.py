from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.usuario_service import UsuarioService
from backend.schemas.usuario import UsuarioCreate, UsuarioResponse, UsuarioUpdate

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


def _service(db: Session) -> UsuarioService:
    return UsuarioService(db)


@router.post(
    "/",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_usuario(data: UsuarioCreate, db: Session = Depends(get_db)):
    service = _service(db)
    return service.criar_usuario(data)


@router.get("/", response_model=list[UsuarioResponse])
def list_usuarios(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    service = _service(db)
    return service.listar_usuarios(skip=skip, limit=limit)


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def get_usuario(usuario_id: int, db: Session = Depends(get_db)):
    service = _service(db)
    return service.obter_usuario_por_id(usuario_id)


@router.put("/{usuario_id}", response_model=UsuarioResponse)
def update_usuario(
    usuario_id: int, data: UsuarioUpdate, db: Session = Depends(get_db)
):
    service = _service(db)
    return service.atualizar_usuario(usuario_id, data)


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_usuario(usuario_id: int, db: Session = Depends(get_db)):
    service = _service(db)
    service.deletar_usuario(usuario_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

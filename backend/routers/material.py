from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import AuthData, get_current_usuario
from backend.schemas.material import MaterialResponse
from backend.services.material_service import MaterialService

router = APIRouter(prefix="/api/materiais", tags=["Materiais"])


def _service(db: Session = Depends(get_db)) -> MaterialService:
    return MaterialService(db)


@router.get(
    "/disciplina/{disciplina_id}",
    response_model=list[MaterialResponse],
)
async def listar_materiais(
    disciplina_id: int,
    auth_data: AuthData = Depends(get_current_usuario),
    service: MaterialService = Depends(_service),
):
    return service.listar_materiais(disciplina_id)


@router.post(
    "/disciplina/{disciplina_id}/upload",
    response_model=MaterialResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_material(
    disciplina_id: int,
    file: UploadFile = File(...),
    descricao: Optional[str] = Form(None),
    auth_data: AuthData = Depends(get_current_usuario),
    service: MaterialService = Depends(_service),
):
    if auth_data.usuario.tipo_perfil not in ("professor", "servidor", "admin", "psicopedagogo"):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas professores e servidores podem enviar materiais",
        )
    return await service.upload_material(
        disciplina_id=disciplina_id,
        usuario_id=auth_data.usuario.id,
        file=file,
        descricao=descricao,
    )


@router.get("/{material_id}/download")
async def download_material(
    material_id: int,
    auth_data: AuthData = Depends(get_current_usuario),
    service: MaterialService = Depends(_service),
):
    file_path, nome_original = service.obter_caminho_arquivo(material_id)
    return FileResponse(
        path=str(file_path),
        filename=nome_original,
        media_type="application/octet-stream",
    )


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_material(
    material_id: int,
    auth_data: AuthData = Depends(get_current_usuario),
    service: MaterialService = Depends(_service),
):
    service.deletar_material(
        material_id=material_id,
        usuario_id=auth_data.usuario.id,
        tipo_perfil=auth_data.usuario.tipo_perfil,
    )
    return None

from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import AuthData, get_current_usuario, require_napne, require_admin
from backend.services.aluno_service import AlunoService
from backend.schemas.aluno import AlunoBuscaResultado, AlunoCreate, AlunoResponse, AlunoUpdate
from backend.schemas.perfil_aluno import PerfilAlunoCreate, PerfilAlunoResponse, PerfilAlunoUpdate

router = APIRouter(prefix="/alunos", tags=["Aluno"])


def _service(db: Session) -> AlunoService:
    return AlunoService(db)


@router.post(
    "/",
    response_model=AlunoResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_aluno(
    data: AlunoCreate,
    auth_data: AuthData = Depends(require_napne),
    db: Session = Depends(get_db),
):
    service = _service(db)
    return service.criar_aluno(data)


@router.get("/", response_model=list[AlunoResponse])
def list_alunos(
    skip: int = 0,
    limit: int = 100,
    auth_data: AuthData = Depends(require_napne),
    db: Session = Depends(get_db),
):
    service = _service(db)
    return service.listar_alunos(skip=skip, limit=limit)


@router.get("/busca", response_model=list[AlunoBuscaResultado])
def buscar_alunos(
    q: str = Query(..., min_length=2, max_length=100),
    auth_data: AuthData = Depends(get_current_usuario),
    db: Session = Depends(get_db),
):
    if auth_data.usuario.tipo_perfil == "aluno":
        raise HTTPException(status_code=403, detail="Acesso restrito a servidores e professores.")
    service = _service(db)
    return service.buscar_alunos(q)


@router.get("/{aluno_id}", response_model=AlunoResponse)
def get_aluno(
 aluno_id: int,
 auth_data: AuthData = Depends(require_napne),
 db: Session = Depends(get_db),
):
    service = _service(db)
    return service.obter_aluno_por_id(aluno_id)


@router.put("/{aluno_id}", response_model=AlunoResponse)
def update_aluno(
    aluno_id: int,
    data: AlunoUpdate,
    auth_data: AuthData = Depends(require_napne),
    db: Session = Depends(get_db),
):
    service = _service(db)
    return service.atualizar_aluno(aluno_id, data)


@router.delete("/{aluno_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_aluno(
 aluno_id: int,
 auth_data: AuthData = Depends(require_admin),
 db: Session = Depends(get_db),
):
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
    aluno_id: int,
    data: PerfilAlunoCreate,
    auth_data: AuthData = Depends(require_napne),
    db: Session = Depends(get_db),
):
    service = _service(db)
    return service.criar_perfil(aluno_id, data)


@router.get(
 "/{aluno_id}/perfil", response_model=PerfilAlunoResponse
)
def get_perfil(
 aluno_id: int,
 auth_data: AuthData = Depends(require_napne),
 db: Session = Depends(get_db),
):
    service = _service(db)
    return service.obter_perfil(aluno_id)


@router.put(
    "/{aluno_id}/perfil", response_model=PerfilAlunoResponse
)
def update_perfil(
    aluno_id: int,
    data: PerfilAlunoUpdate,
    auth_data: AuthData = Depends(require_napne),
    db: Session = Depends(get_db),
):
    service = _service(db)
    return service.atualizar_perfil(aluno_id, data)


@router.get("/export/csv")
def exportar_alunos_csv(
    auth_data: AuthData = Depends(require_napne),
    db: Session = Depends(get_db),
):
    """
    Exporta lista de alunos em formato CSV.
    Apenas equipe NAPNE pode exportar.
    """
    try:
        service = _service(db)
        alunos = service.listar_alunos(skip=0, limit=10000)
        
        # Criar buffer CSV
        output = io.StringIO()
        writer = csv.writer(output, delimiter=";", lineterminator="\n")
        
        # Header
        writer.writerow([
            "id", "matricula", "nome", "email", "curso",
            "campus", "status_acompanhamento", "diagnostico"
        ])
        
        # Rows
        for aluno in alunos:
            writer.writerow([
                aluno.id,
                aluno.matricula or "",
                aluno.nome,
                aluno.email or "",
                aluno.curso or "",
                aluno.campus or "",
                aluno.status_acompanhamento or "",
                (aluno.perfil.diagnostico if aluno.perfil else "") or "",
            ])
        
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=alunos.csv"},
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao exportar CSV: {str(e)}")

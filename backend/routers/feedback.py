from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import AuthData, get_current_usuario
from backend.repositories.conteudo_feedback import ConteudoFeedbackRepository
from backend.schemas.conteudo_feedback import ConteudoFeedbackCreate, ConteudoFeedbackResponse

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])


def _repository(db: Session = Depends(get_db)) -> ConteudoFeedbackRepository:
    return ConteudoFeedbackRepository(db)


@router.get("/conteudos/{conteudo_id}", response_model=list[ConteudoFeedbackResponse])
async def listar_feedbacks(
    conteudo_id: int,
    auth_data: AuthData = Depends(get_current_usuario),
    db: Session = Depends(_repository),
):
    """Lista todos os feedbacks de um conteúdo gerado por IA."""
    repo: ConteudoFeedbackRepository = db
    feedbacks = repo.listar_por_conteudo(conteudo_id)
    
    # Construir resposta com nomes
    result = []
    for fb in feedbacks:
        result.append(
            ConteudoFeedbackResponse(
                id=fb.id,
                conteudo_id=fb.conteudo_id,
                professor_id=fb.professor_id,
                professor_nome=fb.professor.nome if fb.professor else None,
                disciplina_id=fb.disciplina_id,
                disciplina_sigla=fb.disciplina.sigla if fb.disciplina else None,
                avaliacao=fb.avaliacao,
                comentario=fb.comentario,
                criado_em=fb.criado_em,
            )
        )
    return result


@router.post("/conteudos/{conteudo_id}", response_model=ConteudoFeedbackResponse, status_code=status.HTTP_200_OK)
async def criar_feedback(
    conteudo_id: int,
    data: ConteudoFeedbackCreate,
    auth_data: AuthData = Depends(get_current_usuario),
    db: Session = Depends(_repository),
):
    """
    Cria ou atualiza feedback de um professor para um conteúdo.
    
    Um professor só pode dar um feedback por conteúdo/disciplina (upsert).
    """
    repo: ConteudoFeedbackRepository = db
    
    # Validar se professor tem permissão (deve ser professor ou NAPNE)
    if auth_data.usuario.tipo_perfil not in ("professor", "psicopedagogo", "servidor", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas professores e equipe NAPNE podem avaliar conteúdos",
        )
    
    feedback = repo.criar_ou_atualizar(
        conteudo_id=conteudo_id,
        professor_id=auth_data.usuario.id,
        avaliacao=data.avaliacao,
        utilidade_percebida=data.utilidade_percebida,
        disciplina_id=data.disciplina_id,
        comentario=data.comentario,
    )
    
    return ConteudoFeedbackResponse(
        id=feedback.id,
        conteudo_id=feedback.conteudo_id,
        professor_id=feedback.professor_id,
        professor_nome=feedback.professor.nome if feedback.professor else None,
        disciplina_id=feedback.disciplina_id,
        disciplina_sigla=feedback.disciplina.sigla if feedback.disciplina else None,
        avaliacao=feedback.avaliacao,
        utilidade_percebida=feedback.utilidade_percebida,
        comentario=feedback.comentario,
        criado_em=feedback.criado_em,
    )
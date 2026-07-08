from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import AuthData, require_napne
from backend.models.conteudo_gerado import ConteudoGerado
from backend.models.conteudo_feedback import ConteudoFeedback
from backend.models.usuario import Usuario
from backend.models.aluno import Aluno

router = APIRouter(prefix="/api/relatorios", tags=["Relatorios"])


@router.get("/uso/csv")
async def relatorio_uso_csv(
    data_inicio: Optional[str] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    data_fim: Optional[str] = Query(None, description="Data final (YYYY-MM-DD)"),
    auth_data: AuthData = Depends(require_napne),
    db: Session = Depends(get_db),
):
    """
    Relatório de uso do sistema para NAPNE.
    Exporta CSV com: conteúdos gerados, feedbacks, utilidade média, professores ativos.
    """
    # Parse datas
    inicio = None
    fim = None
    if data_inicio:
        try:
            inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
        except ValueError:
            inicio = None
    if data_fim:
        try:
            fim = datetime.strptime(data_fim, "%Y-%m-%d") + timedelta(days=1)
        except ValueError:
            fim = None
    
    # Query de conteúdos gerados
    query = db.query(
        ConteudoGerado.id,
        ConteudoGerado.tema,
        ConteudoGerado.modelo_ia,
        ConteudoGerado.gerado_em,
        Usuario.nome.label("usuario_nome"),
        Usuario.tipo_perfil.label("usuario_tipo"),
        Aluno.nome.label("aluno_nome"),
        Aluno.matricula.label("aluno_matricula"),
    ).outerjoin(Usuario, ConteudoGerado.usuario_id == Usuario.id)\
     .join(Aluno, ConteudoGerado.aluno_id == Aluno.id)
    
    if inicio:
        query = query.filter(ConteudoGerado.gerado_em >= inicio)
    if fim:
        query = query.filter(ConteudoGerado.gerado_em < fim)
    
    conteudos = query.all()
    
    # Query de feedbacks com utilidade média
    feedbacks_query = db.query(
        ConteudoFeedback.conteudo_id,
        func.count(ConteudoFeedback.id).label("total_feedbacks"),
        func.avg(ConteudoFeedback.utilidade_percebida).label("utilidade_media"),
    ).group_by(ConteudoFeedback.conteudo_id)
    
    if inicio or fim:
        feedbacks_query = feedbacks_query.join(ConteudoGerado, ConteudoFeedback.conteudo_id == ConteudoGerado.id)
        if inicio:
            feedbacks_query = feedbacks_query.filter(ConteudoGerado.gerado_em >= inicio)
        if fim:
            feedbacks_query = feedbacks_query.filter(ConteudoGerado.gerado_em < fim)
    
    try:
        feedbacks_stats = {fb.conteudo_id: fb for fb in feedbacks_query.all()}
    except Exception:
        # Quando a tabela conteudo_feedback ainda não existe (ex.: ambiente de desenvolvimento), continuar com stats vazios
        feedbacks_stats = {}

    
    # Criar CSV
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", lineterminator="\n")
    
    # Header
    writer.writerow([
        "id_conteudo", "tema", "modelo_ia", "gerado_em",
        "usuario_nome", "usuario_tipo",
        "aluno_nome", "aluno_matricula",
        "total_feedbacks", "utilidade_media",
        "avaliacao_predominante"
    ])
    
    # Rows
    for c in conteudos:
        stats = feedbacks_stats.get(c.id)
        total_feedbacks = stats.total_feedbacks if stats else 0
        utilidade_media = round(stats.utilidade_media, 2) if stats and stats.utilidade_media else None
        
        # Obter avaliação predominante
        if stats:
            feedbacks_do_conteudo = db.query(ConteudoFeedback.avaliacao).filter(
                ConteudoFeedback.conteudo_id == c.id
            ).all()
            contagem = {}
            for fb in feedbacks_do_conteudo:
                contagem[fb.avaliacao] = contagem.get(fb.avaliacao, 0) + 1
            avaliacao_predominante = max(contagem, key=contagem.get) if contagem else None
        else:
            avaliacao_predominante = None
        
        writer.writerow([
            c.id,
            c.tema,
            c.modelo_ia,
            c.gerado_em.strftime("%Y-%m-%d %H:%M:%S") if c.gerado_em else None,
            c.usuario_nome,
            c.usuario_tipo,
            c.aluno_nome,
            c.aluno_matricula,
            total_feedbacks,
            utilidade_media,
            avaliacao_predominante,
        ])
    
    output.seek(0)
    
    data_range = f"{data_inicio or 'inicio'}_a_{data_fim or 'hoje'}"
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=relatorio-uso-{data_range}.csv"},
    )


@router.get("/resumo")
async def resumo_metricas(
    data_inicio: Optional[str] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    data_fim: Optional[str] = Query(None, description="Data final (YYYY-MM-DD)"),
    auth_data: AuthData = Depends(require_napne),
    db: Session = Depends(get_db),
):
    """
    Retorna métricas agregadas de uso para o dashboard NAPNE.
    """
    # Parse datas
    inicio = None
    fim = None
    if data_inicio:
        try:
            inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
        except ValueError:
            inicio = None
    if data_fim:
        try:
            fim = datetime.strptime(data_fim, "%Y-%m-%d") + timedelta(days=1)
        except ValueError:
            fim = None
    
    # Query base
    query = db.query(ConteudoGerado)
    if inicio:
        query = query.filter(ConteudoGerado.gerado_em >= inicio)
    if fim:
        query = query.filter(ConteudoGerado.gerado_em < fim)
    
    # Total de conteúdos gerados
    total_conteudos = query.count()
    
    # Total de feedbacks
    feedbacks_query = db.query(ConteudoFeedback)
    if inicio or fim:
        feedbacks_query = feedbacks_query.join(ConteudoGerado)
        if inicio:
            feedbacks_query = feedbacks_query.filter(ConteudoGerado.gerado_em >= inicio)
        if fim:
            feedbacks_query = feedbacks_query.filter(ConteudoGerado.gerado_em < fim)
    
    total_feedbacks = feedbacks_query.count()
    
    # Utilidade média
    utilidade_media_query = db.query(func.avg(ConteudoFeedback.utilidade_percebida))
    if inicio or fim:
        utilidade_media_query = utilidade_media_query.join(ConteudoGerado)
        if inicio:
            utilidade_media_query = utilidade_media_query.filter(ConteudoGerado.gerado_em >= inicio)
        if fim:
            utilidade_media_query = utilidade_media_query.filter(ConteudoGerado.gerado_em < fim)
    
    utilidade_media = utilidade_media_query.scalar()
    
    # Professores ativos (único)
    professores_ativos_query = db.query(func.count(func.distinct(ConteudoGerado.usuario_id)))
    if inicio:
        professores_ativos_query = professores_ativos_query.filter(ConteudoGerado.gerado_em >= inicio)
    if fim:
        professores_ativos_query = professores_ativos_query.filter(ConteudoGerado.gerado_em < fim)
    
    professores_ativos = professores_ativos_query.scalar() or 0
    
    # Taxa de feedback (feedbacks / conteúdos)
    taxa_feedback = (total_feedbacks / total_conteudos * 100) if total_conteudos > 0 else 0
    
    return {
        "total_conteudos": total_conteudos,
        "total_feedbacks": total_feedbacks,
        "utilidade_media": round(utilidade_media, 2) if utilidade_media else None,
        "professores_ativos": professores_ativos,
        "taxa_feedback": round(taxa_feedback, 1),
        "periodo": {
            "inicio": data_inicio,
            "fim": data_fim,
        }
    }
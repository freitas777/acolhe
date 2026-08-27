from __future__ import annotations

import csv
import io
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from backend.database import get_db
from backend.dependencies import AuthData, require_napne
from backend.models.acomodacao_observacao import AcomodacaoObservacao
from backend.models.aluno import Aluno
from backend.models.conteudo_gerado import ConteudoGerado
from backend.models.conteudo_feedback import ConteudoFeedback
from backend.models.conversa import Conversa
from backend.models.diario_aluno import DiarioAluno
from backend.models.disciplina import Disciplina
from backend.models.material import Material
from backend.models.usuario import Usuario

logger = logging.getLogger(__name__)

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


@router.get("/aluno/{aluno_id}/pdf")
async def relatorio_aluno_pdf(
    aluno_id: int,
    auth_data: AuthData = Depends(require_napne),
    db: Session = Depends(get_db),
):
    aluno = (
        db.query(Aluno)
        .options(selectinload(Aluno.perfil))
        .filter(Aluno.id == aluno_id)
        .first()
    )
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno nao encontrado")

    perfil = aluno.perfil

    conteudos = (
        db.query(ConteudoGerado)
        .filter(ConteudoGerado.aluno_id == aluno_id)
        .order_by(ConteudoGerado.gerado_em.desc())
        .limit(50)
        .all()
    )

    observacoes = (
        db.query(AcomodacaoObservacao)
        .options(
            selectinload(AcomodacaoObservacao.disciplina),
            selectinload(AcomodacaoObservacao.professor),
        )
        .filter(AcomodacaoObservacao.aluno_id == aluno_id)
        .order_by(AcomodacaoObservacao.criado_em.desc())
        .all()
    )

    diarios = (
        db.query(DiarioAluno)
        .filter(DiarioAluno.aluno_id == aluno_id)
        .all()
    )
    disciplina_ids = [d.disciplina_id for d in diarios]

    materiais = []
    if disciplina_ids:
        materiais = (
            db.query(Material)
            .options(selectinload(Material.disciplina))
            .filter(Material.disciplina_id.in_(disciplina_ids))
            .order_by(Material.criado_em.desc())
            .all()
        )

    conversas = (
        db.query(Conversa)
        .options(selectinload(Conversa.disciplina), selectinload(Conversa.mensagens))
        .filter(Conversa.aluno_id == aluno_id)
        .order_by(Conversa.criada_em.desc())
        .limit(50)
        .all()
    )

    try:
        from fpdf import FPDF

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()

        data_geracao = datetime.now().strftime("%d/%m/%Y %H:%M")

        # Titulo
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(10, 127, 112)
        pdf.cell(0, 12, "Relatorio Individual do Aluno", new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(10, 127, 112)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)

        # Data geracao
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 6, f"Gerado em: {data_geracao}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(6)

        # Dados do Aluno
        _pdf_section_header(pdf, "Dados do Aluno")
        _pdf_info_row(pdf, "Nome:", aluno.nome)
        if aluno.matricula:
            _pdf_info_row(pdf, "Matricula:", aluno.matricula)
        if aluno.curso:
            _pdf_info_row(pdf, "Curso:", aluno.curso)
        if aluno.campus:
            _pdf_info_row(pdf, "Campus:", aluno.campus)
        if aluno.email:
            _pdf_info_row(pdf, "Email:", aluno.email)
        _pdf_info_row(pdf, "Status:", aluno.status_acompanhamento or "")
        _pdf_info_row(pdf, "Cadastrado em:", aluno.criado_em.strftime("%d/%m/%Y") if aluno.criado_em else "N/A")
        pdf.ln(4)

        # Perfil Pedagogico
        _pdf_section_header(pdf, "Perfil Pedagogico")
        if perfil:
            if perfil.nivel_atencao:
                _pdf_info_row(pdf, "Nivel de Atencao:", perfil.nivel_atencao.value.upper())
            _pdf_info_row(pdf, "Dificuldade de Leitura:", "SIM" if perfil.dificuldade_leitura else "NAO")
            if perfil.preferencia:
                _pdf_info_row(pdf, "Preferencia de Aprendizado:", perfil.preferencia.value)
            if perfil.interesses:
                _pdf_info_row(pdf, "Interesses:", perfil.interesses)
            if perfil.diagnostico:
                _pdf_info_row(pdf, "Diagnostico:", perfil.diagnostico)
        else:
            pdf.set_font("Helvetica", "I", 10)
            pdf.set_text_color(150, 150, 150)
            pdf.cell(0, 6, "Sem perfil cadastrado.", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # Conteudos Gerados pela IA
        _pdf_section_header(pdf, "Conteudos Gerados pela IA")
        if conteudos:
            _pdf_table_header(pdf, ["Data", "Tema", "Modelo IA", "Versao"], [35, 80, 45, 20])
            for c in conteudos:
                data = c.gerado_em.strftime("%d/%m/%Y %H:%M") if c.gerado_em else "N/A"
                _pdf_table_row(pdf, [data, c.tema, c.modelo_ia, str(c.versao)], [35, 80, 45, 20])
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 5, f"Total: {len(conteudos)} conteudo(s) gerado(s)", new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.set_font("Helvetica", "I", 10)
            pdf.set_text_color(150, 150, 150)
            pdf.cell(0, 6, "Nenhum conteudo gerado.", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # Observacoes dos Professores
        _pdf_section_header(pdf, "Observacoes dos Professores")
        if observacoes:
            _pdf_table_header(pdf, ["Data", "Disciplina", "Professor", "Observacao"], [25, 25, 35, 95])
            for obs in observacoes:
                data = obs.criado_em.strftime("%d/%m/%Y") if obs.criado_em else "N/A"
                disc = obs.disciplina.sigla if obs.disciplina else "N/A"
                prof = obs.professor.nome if obs.professor else "N/A"
                _pdf_table_row(pdf, [data, disc, prof, obs.texto], [25, 25, 35, 95])
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 5, f"Total: {len(observacoes)} observacao(oes)", new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.set_font("Helvetica", "I", 10)
            pdf.set_text_color(150, 150, 150)
            pdf.cell(0, 6, "Nenhuma observacao registrada.", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # Materiais das Disciplinas
        _pdf_section_header(pdf, "Materiais das Disciplinas")
        if materiais:
            _pdf_table_header(pdf, ["Disciplina", "Arquivo", "Categoria", "Data"], [55, 65, 30, 30])
            for mat in materiais:
                disc = mat.disciplina.descricao if mat.disciplina else "N/A"
                data = mat.criado_em.strftime("%d/%m/%Y") if mat.criado_em else "N/A"
                _pdf_table_row(pdf, [disc, mat.nome_original, mat.categoria, data], [55, 65, 30, 30])
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 5, f"Total: {len(materiais)} material(is)", new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.set_font("Helvetica", "I", 10)
            pdf.set_text_color(150, 150, 150)
            pdf.cell(0, 6, "Nenhum material vinculado as disciplinas do aluno.", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # Historico de Conversas
        _pdf_section_header(pdf, "Historico de Conversas")
        if conversas:
            _pdf_table_header(pdf, ["Data", "Titulo", "Disciplina", "Msgs"], [35, 65, 60, 20])
            for conv in conversas:
                data = conv.criada_em.strftime("%d/%m/%Y %H:%M") if conv.criada_em else "N/A"
                disc = conv.disciplina.descricao if conv.disciplina else "Geral"
                n_msgs = str(len(conv.mensagens)) if conv.mensagens else "0"
                _pdf_table_row(pdf, [data, conv.titulo, disc, n_msgs], [35, 65, 60, 20])
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 5, f"Total: {len(conversas)} conversa(s)", new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.set_font("Helvetica", "I", 10)
            pdf.set_text_color(150, 150, 150)
            pdf.cell(0, 6, "Nenhuma conversa registrada.", new_x="LMARGIN", new_y="NEXT")

        # Footer
        pdf.ln(10)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 5, f"Acolhe+ - Sistema de Apoio a Educacao Inclusiva | IFRN | Relatorio gerado em {data_geracao}", align="C", new_x="LMARGIN", new_y="NEXT")

        pdf_bytes = pdf.output()
        pdf_buffer = io.BytesIO(pdf_bytes)
        pdf_buffer.seek(0)
        nome_arquivo = f"relatorio-{aluno.nome.replace(' ', '-').lower()}-{datetime.now().strftime('%Y%m%d')}.pdf"

        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{nome_arquivo}"'},
        )
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Biblioteca fpdf2 nao instalada. Execute: pip install fpdf2",
        )


def _pdf_section_header(pdf, title: str):
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(10, 127, 112)
    pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(220, 220, 220)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)


def _pdf_info_row(pdf, label: str, value: str):
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(85, 85, 85)
    pdf.cell(45, 6, label, new_x="RIGHT", new_y="TOP")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(51, 51, 51)
    pdf.cell(0, 6, str(value or ""), new_x="LMARGIN", new_y="NEXT")


def _pdf_table_header(pdf, headers: list, widths: list):
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(10, 127, 112)
    pdf.set_text_color(255, 255, 255)
    for i, h in enumerate(headers):
        pdf.cell(widths[i], 7, h, border=1, fill=True, new_x="RIGHT", new_y="TOP")
    pdf.ln()


def _pdf_table_row(pdf, cells: list, widths: list):
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(51, 51, 51)
    if pdf.get_y() > 265:
        pdf.add_page()
    max_h = 6
    for i, c in enumerate(cells):
        text = str(c or "")
        if len(text) > 40:
            text = text[:37] + "..."
        pdf.cell(widths[i], max_h, text, border=1, new_x="RIGHT", new_y="TOP")
    pdf.ln()
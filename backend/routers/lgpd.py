from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, selectinload

from backend.database import get_db
from backend.dependencies import AuthData, get_current_usuario
from backend.models.aluno import Aluno
from backend.models.usuario import Usuario
from backend.models.perfil_aluno import PerfilAluno
from backend.models.conteudo_gerado import ConteudoGerado
from backend.models.acomodacao_observacao import AcomodacaoObservacao
from backend.models.conversa import Conversa
from backend.models.mensagem import Mensagem
from backend.models.notificacao import Notificacao
from backend.models.audit_log import AuditLog

router = APIRouter(prefix="/api/lgpd", tags=["LGPD"])


@router.get("/export/meus-dados")
async def export_meus_dados(
    auth_data: AuthData = Depends(get_current_usuario),
    db: Session = Depends(get_db),
):
    """
    Exporta todos os dados pessoais do usuário autenticado (LGPD Art. 18).
    Retorna um ZIP com CSVs de cada categoria de dados.
    """
    usuario = db.query(Usuario).options(
        selectinload(Usuario.conta_local)
    ).filter(Usuario.id == auth_data.usuario.id).first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    
    # Coletar dados
    dados_pessoais = {
        "id": usuario.id,
        "suap_id": usuario.suap_id,
        "nome": usuario.nome,
        "email": usuario.email,
        "matricula": usuario.matricula,
        "campus": usuario.campus,
        "tipo_vinculo": usuario.tipo_vinculo,
        "tipo_perfil": usuario.tipo_perfil,
        "setor": usuario.setor,
        "aprovado_napne": usuario.aprovado_napne,
        "criado_em": usuario.criado_em.isoformat() if usuario.criado_em else None,
    }
    
    # Conteúdos gerados
    conteudos = db.query(ConteudoGerado).filter(
        ConteudoGerado.usuario_id == usuario.id
    ).all()
    
    # Conversas e mensagens
    conversas = db.query(Conversa).options(
        selectinload(Conversa.mensagens)
    ).filter(Conversa.usuario_id == usuario.id).all()
    
    # Notificações
    notificacoes = db.query(Notificacao).filter(
        Notificacao.destino_tipo == "usuario",
        Notificacao.destino_id == usuario.id
    ).all()
    
    # Audit logs
    audit_logs = db.query(AuditLog).filter(
        AuditLog.usuario == usuario.id
    ).all()
    
    # Criar JSON com todos os dados
    export_data = {
        "data_exportacao": datetime.utcnow().isoformat(),
        "usuario": dados_pessoais,
        "conteudos_gerados": [
            {
                "id": c.id,
                "aluno_id": c.aluno_id,
                "tema": c.tema,
                "prompt_utilizado": c.prompt_utilizado,
                "conteudo": c.conteudo,
                "modelo_ia": c.modelo_ia,
                "gerado_em": c.gerado_em.isoformat() if c.gerado_em else None,
            }
            for c in conteudos
        ],
        "conversas": [
            {
                "id": conv.id,
                "aluno_id": conv.aluno_id,
                "titulo": conv.titulo,
                "criado_em": conv.criado_em.isoformat() if conv.criado_em else None,
                "mensagens": [
                    {
                        "id": m.id,
                        "conteudo": m.conteudo,
                        "remetente": m.remetente,
                        "criado_em": m.criado_em.isoformat() if m.criado_em else None,
                    }
                    for m in conv.mensagens
                ],
            }
            for conv in conversas
        ],
        "notificacoes": [
            {
                "id": n.id,
                "titulo": n.titulo,
                "mensagem": n.mensagem,
                "tipo": n.tipo,
                "criada_em": n.criada_em.isoformat() if n.criada_em else None,
            }
            for n in notificacoes
        ],
        "audit_logs": [
            {
                "id": log.id,
                "acao": log.acao,
                "recurso_tipo": log.recurso_tipo,
                "recurso_id": log.recurso_id,
                "aluno_id": log.aluno_id,
                "detalhes": log.detalhes,
                "criado_em": log.criado_em.isoformat() if log.criado_em else None,
            }
            for log in audit_logs
        ],
    }
    
    # Converter para JSON
    json_output = io.StringIO()
    json.dump(export_data, json_output, indent=2, ensure_ascii=False)
    json_output.seek(0)
    
    return StreamingResponse(
        json_output,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=meus-dados-{usuario.id}.json"},
    )


@router.get("/export/aluno/{aluno_id}")
async def export_dados_aluno(
    aluno_id: int,
    auth_data: AuthData = Depends(get_current_usuario),
    db: Session = Depends(get_db),
):
    """
    Exporta todos os dados de um aluno (LGPD Art. 18).
    Apenas equipe NAPNE pode exportar.
    """
    # Verificar permissão
    if auth_data.usuario.tipo_perfil not in ("psicopedagogo", "servidor", "admin"):
        raise HTTPException(
            status_code=403,
            detail="Apenas equipe NAPNE pode exportar dados de alunos",
        )
    
    aluno = db.query(Aluno).options(
        selectinload(Aluno.perfil),
        selectinload(Aluno.conteudos),
    ).filter(Aluno.id == aluno_id).first()
    
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno nao encontrado")
    
    # Observações
    observacoes = db.query(AcomodacaoObservacao).filter(
        AcomodacaoObservacao.aluno_id == aluno_id
    ).all()
    
    # Criar JSON
    export_data = {
        "data_exportacao": datetime.utcnow().isoformat(),
        "aluno": {
            "id": aluno.id,
            "matricula": aluno.matricula,
            "nome": aluno.nome,
            "email": aluno.email,
            "curso": aluno.curso,
            "campus": aluno.campus,
            "status_acompanhamento": aluno.status_acompanhamento,
            "diagnostico": aluno.diagnostico,
        },
        "perfil": {
            "nivel_atencao": aluno.perfil.nivel_atencao if aluno.perfil else None,
            "dificuldade_leitura": aluno.perfil.dificuldade_leitura if aluno.perfil else None,
            "preferencia": aluno.perfil.preferencia if aluno.perfil else None,
            "interesses": aluno.perfil.interesses if aluno.perfil else None,
        } if aluno.perfil else None,
        "conteudos_gerados": [
            {
                "id": c.id,
                "tema": c.tema,
                "modelo_ia": c.modelo_ia,
                "gerado_em": c.gerado_em.isoformat() if c.gerado_em else None,
            }
            for c in aluno.conteudos
        ],
        "observacoes": [
            {
                "id": obs.id,
                "disciplina_sigla": obs.disciplina_sigla,
                "professor_nome": obs.professor_nome,
                "texto": obs.texto,
                "criado_em": obs.criado_em.isoformat() if obs.criado_em else None,
            }
            for obs in observacoes
        ],
    }
    
    json_output = io.StringIO()
    json.dump(export_data, json_output, indent=2, ensure_ascii=False)
    json_output.seek(0)
    
    return StreamingResponse(
        json_output,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=aluno-{aluno_id}-dados.json"},
    )
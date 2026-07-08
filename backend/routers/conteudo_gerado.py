from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import AuthData, get_current_usuario, require_napne, require_admin
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
def create_conteudo(
    data: ConteudoGeradoCreate,
    auth_data: AuthData = Depends(require_napne),
    db: Session = Depends(get_db),
):
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
 auth_data: AuthData = Depends(require_napne),
 db: Session = Depends(get_db),
):
    if aluno_id:
        return _conteudo_repo(db).list_by_aluno(aluno_id)
    return _conteudo_repo(db).list_all(skip=skip, limit=limit)


@router.get("/{conteudo_id}", response_model=ConteudoGeradoResponse)
def get_conteudo(
 conteudo_id: int,
 auth_data: AuthData = Depends(require_napne),
 db: Session = Depends(get_db),
):
    conteudo = _conteudo_repo(db).get_by_id(conteudo_id)
    if not conteudo:
        raise HTTPException(
            status_code=404, detail="Conteudo nao encontrado"
        )
    return conteudo


@router.put("/{conteudo_id}", response_model=ConteudoGeradoResponse)
def update_conteudo(
    conteudo_id: int,
    data: ConteudoGeradoUpdate,
    auth_data: AuthData = Depends(require_napne),
    db: Session = Depends(get_db),
):
    payload = data.model_dump(exclude_unset=True)
    updated = _conteudo_repo(db).update(conteudo_id, payload)
    if not updated:
        raise HTTPException(
            status_code=404, detail="Conteudo nao encontrado"
        )
    return updated


@router.delete(
  "/{conteudo_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_conteudo(
  conteudo_id: int,
  auth_data: AuthData = Depends(require_admin),
  db: Session = Depends(get_db),
):
  deleted = _conteudo_repo(db).delete(conteudo_id)
  if not deleted:
    raise HTTPException(
      status_code=404, detail="Conteudo nao encontrado"
    )
  return Response(status_code=status.HTTP_204_NO_CONTENT)


class ConteudoIteracaoRequest(BaseModel):
  """Request para criar nova iteração de conteúdo."""
  novo_prompt: str


@router.post(
  "/{conteudo_id}/iteracao",
  response_model=ConteudoGeradoResponse,
  status_code=status.HTTP_201_CREATED,
)
def criar_iteracao(
  conteudo_id: int,
  data: ConteudoIteracaoRequest,
  auth_data: AuthData = Depends(require_napne),
  db: Session = Depends(get_db),
):
  """
  Cria nova iteração de um conteúdo gerado por IA.
  
  O professor pode solicitar uma nova versão com ajustes (ex: "mais atividades visuais").
  A nova versão herda o tema, mas usa um prompt refinado.
  """
  from backend.services.ai_service import AIService
  from backend.repositories.perfil_aluno import PerfilAlunoRepository
  
  # Conteúdo original (pai)
  conteudo_pai = _conteudo_repo(db).get_by_id(conteudo_id)
  if not conteudo_pai:
    raise HTTPException(status_code=404, detail="Conteudo nao encontrado")
  
  # Herdar aluno_id do conteúdo original
  aluno_id = conteudo_pai.aluno_id
  
  # Perfil do aluno
  perfil = PerfilAlunoRepository(db).get_by_aluno_id(aluno_id)
  
  # Construir prompt com contexto + refinamento
  prompt_completo = f"{data.novo_prompt}\n\nContexto do aluno:\n"
  if perfil:
    if perfil.nivel_atencao:
      prompt_completo += f"- Nível de atenção: {perfil.nivel_atencao}\n"
    if perfil.dificuldade_leitura:
      prompt_completo += f"- Dificuldade de leitura: Sim\n"
    if perfil.preferencia:
      prompt_completo += f"- Preferência de aprendizado: {perfil.preferencia}\n"
    if perfil.interesses:
      prompt_completo += f"- Interesses: {perfil.interesses}\n"
  
  # Gerar nova versão com IA
  ai_service = AIService()
  nova_resposta = ai_service.gerar_conteudo_educacional(
    tema=conteudo_pai.tema,
    perfil_aluno={
      "nivel_atencao": perfil.nivel_atencao if perfil else None,
      "dificuldade_leitura": perfil.dificuldade_leitura if perfil else False,
      "preferencia": perfil.preferencia if perfil else None,
      "interesses": perfil.interesses if perfil else None,
    } if perfil else None,
    prompt_personalizado=prompt_completo,
  )
  
  # Criar nova iteração
  nova_iteracao = ConteudoGerado(
    aluno_id=aluno_id,
    usuario_id=auth_data.usuario.id,
    tema=conteudo_pai.tema,
    prompt_utilizado=prompt_completo,
    conteudo=nova_resposta.conteudo,
    modelo_ia=nova_resposta.modelo_ia,
    versao=conteudo_pai.versao + 1,
    conteudo_pai_id=conteudo_id,
  )
  
  db.add(nova_iteracao)
  db.commit()
  db.refresh(nova_iteracao)
  
  return nova_iteracao


@router.get("/{conteudo_id}/historico", response_model=list[ConteudoGeradoResponse])
def listar_historico(
  conteudo_id: int,
  auth_data: AuthData = Depends(get_current_usuario),
  db: Session = Depends(get_db),
):
  """
  Lista todas as iterações de um conteúdo (histórico de refinamentos).
  
  Retorna a árvore completa de versões, da original até as iterações.
  """
  # Encontrar a raiz (primeira versão)
  raiz = _conteudo_repo(db).get_by_id(conteudo_id)
  if not raiz:
    raise HTTPException(status_code=404, detail="Conteudo nao encontrado")
  
  # Se não for a raiz, subir até achar
  while raiz.conteudo_pai_id:
    raiz = _conteudo_repo(db).get_by_id(raiz.conteudo_pai_id)
  
  # Coletar todas as iterações (BFS)
  historico = [raiz]
  fila = [raiz]
  
  while fila:
    atual = fila.pop(0)
    if atual.iteracoes:
      for iteracao in atual.iteracoes:
        historico.append(iteracao)
        fila.append(iteracao)
  
  # Ordenar por data
  historico.sort(key=lambda x: x.gerado_em)
  
  return historico

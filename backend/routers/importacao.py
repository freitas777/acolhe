from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import AuthData, get_current_usuario, require_napne
from backend.models.aluno import Aluno
from backend.repositories.aluno import AlunoRepository
from backend.repositories.pendencia_validacao import PendenciaValidacaoRepository
from backend.schemas.aluno import AlunoSUAPSearchResult, ImportarAlunoRequest, AlunoResponse
from backend.services.suap_service import SUAPService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/importacao", tags=["Importação SUAP"])

DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

_MOCK_ALUNOS = [
    {
        "aluno": {
            "matricula": "123456",
            "nome": "Joao Silva Santos",
            "curso": {"descricao": "Engenharia de Computacao"},
            "campus": {"descricao": "Campus Central"},
            "foto": "",
            "email_pessoal": "joao.silva@email.com",
            "email_academico": "joao.silva@suap.ifrn.edu.br",
            "id": "987654",
            "cpf": "123.456.789-00",
        }
    },
    {
        "aluno": {
            "matricula": "987654",
            "nome": "Maria Oliveira Costa",
            "curso": {"descricao": "Pedagogia"},
            "campus": {"descricao": "Campus Advanced"},
            "foto": "",
            "email_pessoal": "maria.oliveira@email.com",
            "email_academico": "maria.oliveira@suap.ifrn.edu.br",
            "id": "123456",
            "cpf": "987.654.321-00",
        }
    },
    {
        "aluno": {
            "matricula": "456789",
            "nome": "Carlos Eduardo Lima",
            "curso": {"descricao": "Analise e Desenvolvimento de Sistemas"},
            "campus": {"descricao": "Campus Central"},
            "foto": "",
            "email_pessoal": "carlos.lima@email.com",
            "email_academico": "carlos.lima@suap.ifrn.edu.br",
            "id": "456123",
            "cpf": "456.789.123-00",
        }
    },
]


@dataclass
class SUAPSearchResult:
    results: list[AlunoSUAPSearchResult]
    error: Optional[str] = None


@router.get("/buscar", response_model=list[AlunoSUAPSearchResult])
async def buscar_alunos(
    q: str = "",
    matricula: str = "",
    apenas_meu_campus: bool = True,
    auth_data: AuthData = Depends(require_napne),
    db: Session = Depends(get_db),
):
    search_term = matricula or q
    if not search_term or len(search_term) < 2:
        return []

    logger.info(f"[BUSCAR] term='{search_term}' is_matricula={search_term.isdigit()} campus={auth_data.usuario.campus}")

    aluno_repo = AlunoRepository(db)
    usuario_campus = auth_data.usuario.campus or ""

    existing_by_matricula = aluno_repo.get_matricula_lookup()

    results: list[AlunoSUAPSearchResult] = []
    seen: set[str] = set()
    local_found = False

    local_alunos = aluno_repo.buscar_por_nome_ou_matricula(search_term)
    for a in local_alunos:
        if not a.matricula or a.matricula in seen:
            continue
        if not _campus_ok(a.campus, apenas_meu_campus, usuario_campus):
            continue
        seen.add(a.matricula)
        results.append(_local_to_result(a))
        local_found = True

    if not local_found and search_term.isdigit() and len(search_term) >= 4:
        if DEV_MODE:
            mock_results = [r for r in _MOCK_ALUNOS if r["aluno"]["matricula"] == search_term]
            for r in mock_results:
                result = _resumido_to_result(r, existing_by_matricula)
                if result and result.matricula not in seen:
                    seen.add(result.matricula)
                    results.append(result)
        if not results:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="[SUAP_MODULE_ERROR] Sem permissao para acessar dados de alunos no SUAP. O cliente OAuth precisa de acesso ao modulo 'ensino'. Solicite ao administrador do SUAP que habilite esta permissao."
            )

    return results[:50]


def _extract_suap_error(e: httpx.HTTPStatusError) -> str:
    status_code = e.response.status_code
    try:
        error_body = e.response.json()
        detail = error_body.get("detail", "")
        if detail:
            return f"SUAP {status_code}: {detail}"
    except Exception:
        pass

    if status_code == 401:
        return "Token invalido ou expirado. Faca login novamente."
    elif status_code == 403:
        return "Sem permissao para acessar dados de alunos no SUAP. O cliente OAuth precisa de acesso ao modulo 'ensino'. Solicite ao administrador do SUAP que habilite esta permissão."
    elif status_code == 404:
        return "Aluno nao encontrado no SUAP com esta matricula."
    else:
        return f"Erro do SUAP (código {status_code}). Tente novamente."


def _campus_ok(item_campus: str | None, apenas_meu_campus: bool, usuario_campus: str) -> bool:
    if not apenas_meu_campus or not usuario_campus:
        return True
    if not item_campus:
        return True
    def _normalize(s: str) -> str:
        return s.lower().replace("-", " ").replace("  ", " ").strip()
    user_norm = _normalize(usuario_campus)
    item_norm = _normalize(item_campus)
    return user_norm in item_norm or item_norm in user_norm


def _local_to_result(a: Aluno) -> AlunoSUAPSearchResult:
    return AlunoSUAPSearchResult(
        matricula=a.matricula or "",
        nome=a.nome,
        curso=a.curso,
        campus=a.campus,
        foto_url=a.foto_url,
        status_acompanhamento=a.status_acompanhamento,
        ja_importado=True,
        aluno_id=a.id,
    )


def _matriculado_to_result(dados: dict, existing_by_matricula: dict[str, Aluno]) -> AlunoSUAPSearchResult | None:
    matricula = dados.get("matricula", "")
    if not matricula:
        return None

    existing = existing_by_matricula.get(matricula)
    ja_importado = existing is not None

    foto_base64 = dados.get("foto_base64", "")
    mime = dados.get("mime_type", "image/jpeg")
    foto_url = f"data:{mime};base64,{foto_base64}" if foto_base64 else None

    return AlunoSUAPSearchResult(
        matricula=matricula,
        nome=dados.get("nome", ""),
        curso=dados.get("curso", ""),
        campus=dados.get("campus", ""),
        foto_url=foto_url,
        status_acompanhamento=existing.status_acompanhamento if existing else None,
        ja_importado=ja_importado,
        aluno_id=existing.id if existing else None,
    )


def _resumido_to_result(r: dict, existing_by_matricula: dict[str, Aluno]) -> AlunoSUAPSearchResult | None:
    a = r.get("aluno", r)
    matricula = a.get("matricula", "")
    if not matricula:
        return None

    existing = existing_by_matricula.get(matricula)
    ja_importado = existing is not None

    def _extract(obj, key):
        v = obj.get(key, "")
        if isinstance(v, dict):
            return v.get("descricao", "")
        return str(v) if v else ""

    foto_raw = a.get("foto", "")
    foto_url = None
    if foto_raw:
        if foto_raw.startswith("data:") or foto_raw.startswith("http"):
            foto_url = foto_raw
        else:
            foto_url = f"data:image/jpeg;base64,{foto_raw}"

    return AlunoSUAPSearchResult(
        matricula=matricula,
        nome=a.get("nome", ""),
        curso=_extract(a, "curso"),
        campus=_extract(a, "campus"),
        foto_url=foto_url,
        status_acompanhamento=existing.status_acompanhamento if existing else None,
        ja_importado=ja_importado,
        aluno_id=existing.id if existing else None,
    )


@router.post("/importar", response_model=AlunoResponse, status_code=status.HTTP_201_CREATED)
async def importar_aluno(
    request: ImportarAlunoRequest,
    auth_data: AuthData = Depends(require_napne),
    db: Session = Depends(get_db),
):
    if not request.matricula or not request.matricula.strip():
        raise HTTPException(status_code=422, detail="Matricula e obrigatoria.")

    matricula = request.matricula.strip()
    aluno_repo = AlunoRepository(db)

    existing = aluno_repo.get_by_matricula(matricula)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Aluno {matricula} ja importado (status: {existing.status_acompanhamento}).",
        )

    suap = SUAPService()
    token = auth_data.suap_token
    dados = None

    try:
        dados = await suap.get_aluno_matriculado(token, matricula)
    except httpx.HTTPStatusError as e:
        if DEV_MODE and e.response.status_code in (403, 502):
            logger.warning(f"[IMPORTAR] SUAP {e.response.status_code}, usando mock para matricula={matricula}")
            mock_match = [r["aluno"] for r in _MOCK_ALUNOS if r["aluno"]["matricula"] == matricula]
            if mock_match:
                a = mock_match[0]
                dados = {
                    "nome": a.get("nome", ""),
                    "matricula": a.get("matricula", matricula),
                    "curso": a.get("curso", {}).get("descricao", "") if isinstance(a.get("curso"), dict) else a.get("curso", ""),
                    "campus": a.get("campus", {}).get("descricao", "") if isinstance(a.get("campus"), dict) else a.get("campus", ""),
                    "foto_base64": "",
                    "mime_type": "",
                    "email_pessoal": a.get("email_pessoal", ""),
                    "email_academico": a.get("email_academico", ""),
                    "suap_id": str(a.get("id", "")),
                    "cpf": a.get("cpf", ""),
                    "foto_url": "",
                }
        else:
            error_msg = _extract_suap_error(e)
            logger.warning(f"[IMPORTAR] aluno-matriculado HTTP {e.response.status_code}: {error_msg}")
            raise HTTPException(status_code=502, detail=error_msg)
    except Exception as e:
        if DEV_MODE:
            logger.warning(f"[IMPORTAR] Erro de conexao, usando mock para matricula={matricula}")
            mock_match = [r["aluno"] for r in _MOCK_ALUNOS if r["aluno"]["matricula"] == matricula]
            if mock_match:
                a = mock_match[0]
                dados = {
                    "nome": a.get("nome", ""),
                    "matricula": a.get("matricula", matricula),
                    "curso": a.get("curso", {}).get("descricao", "") if isinstance(a.get("curso"), dict) else a.get("curso", ""),
                    "campus": a.get("campus", {}).get("descricao", "") if isinstance(a.get("campus"), dict) else a.get("campus", ""),
                    "foto_base64": "",
                    "mime_type": "",
                    "email_pessoal": a.get("email_pessoal", ""),
                    "email_academico": a.get("email_academico", ""),
                    "suap_id": str(a.get("id", "")),
                    "cpf": a.get("cpf", ""),
                    "foto_url": "",
                }
        else:
            logger.warning(f"[IMPORTAR] aluno-matriculado erro: {type(e).__name__}: {e}")
            raise HTTPException(status_code=502, detail=f"Erro de conexao: {type(e).__name__}")

    if not dados:
        try:
            resumidos = await suap.buscar_alunos_resumido(token, matricula=matricula)
        except Exception as e:
            logger.warning(f"[IMPORTAR] aluno-resumido erro: {type(e).__name__}: {e}")
            resumidos = []
        if resumidos:
            r = resumidos[0]
            a = r.get("aluno", r)

            def _ext(obj, key):
                v = obj.get(key, "")
                return v.get("descricao", "") if isinstance(v, dict) else str(v) if v else ""

            foto_raw = a.get("foto", "")
            foto_url = ""
            if foto_raw:
                foto_url = foto_raw if (foto_raw.startswith("data:") or foto_raw.startswith("http")) else f"data:image/jpeg;base64,{foto_raw}"

            dados = {
                "nome": a.get("nome", ""),
                "matricula": a.get("matricula", matricula),
                "curso": _ext(a, "curso"),
                "campus": _ext(a, "campus"),
                "foto_base64": "",
                "mime_type": "",
                "email_pessoal": a.get("email_pessoal", ""),
                "email_academico": a.get("email_academico", ""),
                "suap_id": str(a.get("id", "")),
                "cpf": a.get("cpf", ""),
                "foto_url": foto_url,
            }

    if not dados:
        raise HTTPException(
            status_code=404,
            detail=f"Aluno com matricula {matricula} nao encontrado no SUAP.",
        )

    nome = dados.get("nome", "").strip()
    if not nome:
        raise HTTPException(status_code=422, detail="Nome do aluno nao encontrado no SUAP.")

    foto_base64 = dados.get("foto_base64", "")
    mime = dados.get("mime_type", "image/jpeg")
    foto_url = dados.get("foto_url", "")
    if foto_base64 and not foto_url:
        foto_url = f"data:{mime};base64,{foto_base64}"

    suap_id = dados.get("suap_id", "") or str(dados.get("id", ""))
    if suap_id and suap_id != "None":
        existing_suap = aluno_repo.get_by_suap_id(suap_id)
        if existing_suap:
            raise HTTPException(
                status_code=409,
                detail=f"Aluno (suap_id={suap_id}) ja importado (status: {existing_suap.status_acompanhamento}).",
            )

    novo = aluno_repo.create({
        "nome": nome,
        "matricula": matricula,
        "suap_id": suap_id if suap_id and suap_id != "None" else None,
        "curso": (dados.get("curso", "") or "").strip(),
        "campus": (dados.get("campus", "") or "").strip(),
        "foto_url": foto_url or None,
        "email": dados.get("email_pessoal", "") or dados.get("email_academico", ""),
        "cpf": dados.get("cpf", ""),
        "status_acompanhamento": "aguardando_indicacao",
        "data_importacao": datetime.utcnow(),
    })
    logger.info(f"[IMPORTAR] Aluno {novo.nome} ({novo.matricula}) importado com sucesso (id={novo.id})")

    pendencia_repo = PendenciaValidacaoRepository(db)
    pendencia_repo.create({
        "aluno_id": novo.id,
        "status": "pendente",
        "motivo": "Aguardando indicacao",
        "criado_em": novo.data_importacao or novo.criado_em,
    })

    return novo
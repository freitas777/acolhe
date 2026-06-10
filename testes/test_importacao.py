from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from backend.models.aluno import Aluno
from backend.routers.importacao import (
    _campus_ok,
    _local_to_result,
    _resumido_to_result,
    _extract_suap_error,
)
from backend.schemas.aluno import AlunoSUAPSearchResult


# ---------------------------------------------------------------------------
# _campus_ok
# ---------------------------------------------------------------------------

class TestCampusOk:
    def test_campus_igual(self):
        assert _campus_ok("Campus Central", True, "Campus Central") is True

    def test_campus_diferente(self):
        assert _campus_ok("Campus Avançado", True, "Campus Central") is False

    def test_nao_filtrar_campus(self):
        assert _campus_ok("Campus X", False, "Campus Y") is True

    def test_usuario_sem_campus(self):
        assert _campus_ok("Campus Central", True, "") is True

    def test_item_sem_campus(self):
        assert _campus_ok(None, True, "Campus Central") is True

    def test_campus_substring(self):
        assert _campus_ok("Campus Central - Natal", True, "Campus Central") is True

    def test_campus_normalizacao_hifen(self):
        assert _campus_ok("Campus-Central", True, "Campus Central") is True


# ---------------------------------------------------------------------------
# _local_to_result
# ---------------------------------------------------------------------------

class TestLocalToResult:
    def test_converte_aluno_local(self):
        aluno = Aluno()
        aluno.id = 1
        aluno.nome = "João"
        aluno.matricula = "123456"
        aluno.curso = "Engenharia"
        aluno.campus = "Campus Central"
        aluno.foto_url = None
        aluno.status_acompanhamento = "ativo"

        result = _local_to_result(aluno)

        assert isinstance(result, AlunoSUAPSearchResult)
        assert result.matricula == "123456"
        assert result.nome == "João"
        assert result.ja_importado is True
        assert result.aluno_id == 1

    def test_aluno_sem_matricula(self):
        aluno = Aluno()
        aluno.id = 2
        aluno.nome = "Maria"
        aluno.matricula = None
        aluno.curso = None
        aluno.campus = None
        aluno.foto_url = None
        aluno.status_acompanhamento = "ativo"

        result = _local_to_result(aluno)

        assert result.matricula == ""


# ---------------------------------------------------------------------------
# _resumido_to_result
# ---------------------------------------------------------------------------

class TestResumidoToResult:
    def test_converte_resumido_com_sucesso(self):
        r = {
            "aluno": {
                "matricula": "123456",
                "nome": "João Silva",
                "curso": {"descricao": "Engenharia"},
                "campus": {"descricao": "Campus Central"},
                "foto": "",
            }
        }
        existing = {}
        result = _resumido_to_result(r, existing)

        assert result is not None
        assert result.matricula == "123456"
        assert result.nome == "João Silva"
        assert result.curso == "Engenharia"
        assert result.ja_importado is False

    def test_sem_matricula_retorna_none(self):
        r = {"aluno": {"nome": "Sem matricula"}}
        result = _resumido_to_result(r, {})
        assert result is None

    def test_aluno_ja_importado(self):
        r = {
            "aluno": {
                "matricula": "123456",
                "nome": "João",
                "curso": {"descricao": "ADS"},
                "campus": {"descricao": "Central"},
                "foto": "",
            }
        }
        existing_aluno = Aluno()
        existing_aluno.id = 10
        existing_aluno.status_acompanhamento = "ativo"
        existing = {"123456": existing_aluno}

        result = _resumido_to_result(r, existing)

        assert result is not None
        assert result.ja_importado is True
        assert result.aluno_id == 10

    def test_foto_base64_adiciona_prefixo(self):
        r = {
            "aluno": {
                "matricula": "123456",
                "nome": "João",
                "foto": "abc123",
            }
        }
        result = _resumido_to_result(r, {})
        assert result.foto_url == "data:image/jpeg;base64,abc123"

    def test_foto_url_nao_adiciona_prefixo(self):
        r = {
            "aluno": {
                "matricula": "123456",
                "nome": "João",
                "foto": "data:image/png;base64,xyz",
            }
        }
        result = _resumido_to_result(r, {})
        assert result.foto_url == "data:image/png;base64,xyz"


# ---------------------------------------------------------------------------
# _extract_suap_error
# ---------------------------------------------------------------------------

class TestExtractSuapError:
    def test_401(self):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {}
        e = MagicMock()
        e.response = mock_response

        result = _extract_suap_error(e)
        assert "Token" in result

    def test_403(self):
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.json.return_value = {}
        e = MagicMock()
        e.response = mock_response

        result = _extract_suap_error(e)
        assert "permissao" in result.lower() or "Sem permissao" in result

    def test_404(self):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {}
        e = MagicMock()
        e.response = mock_response

        result = _extract_suap_error(e)
        assert "nao encontrado" in result.lower()

    def test_com_detail(self):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"detail": "Internal error"}
        e = MagicMock()
        e.response = mock_response

        result = _extract_suap_error(e)
        assert "Internal error" in result

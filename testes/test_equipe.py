from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from backend.models.pendencia_validacao import PendenciaValidacao, StatusPendencia
from backend.models.aluno import Aluno
from backend.models.usuario import Usuario
from backend.services.auth_service import AuthService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_aluno(id: int = 1, nome: str = "João", matricula: str = "123456", status: str = "aguardando_indicacao") -> Aluno:
    a = Aluno()
    a.id = id
    a.nome = nome
    a.matricula = matricula
    a.curso = "Engenharia"
    a.campus = "Campus Central"
    a.status_acompanhamento = status
    a.criado_em = datetime(2024, 1, 1, tzinfo=timezone.utc)
    a.perfil = None
    return a


def make_usuario(id: int = 1, nome: str = "Maria", tipo_perfil: str = "psicopedagogo") -> Usuario:
    u = Usuario()
    u.id = id
    u.nome = nome
    u.email = "maria@escola.edu.br"
    u.tipo_perfil = tipo_perfil
    u.suap_id = "00001"
    u.criado_em = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return u


def make_pendencia(id: int = 1, aluno_id: int = 1, status: StatusPendencia = StatusPendencia.pendente) -> PendenciaValidacao:
    p = PendenciaValidacao()
    p.id = id
    p.aluno_id = aluno_id
    p.status = status
    p.indicado_por_id = 10
    p.validado_por_id = None
    p.validado_em = None
    p.motivo = "Teste"
    p.criado_em = datetime(2024, 1, 1, tzinfo=timezone.utc)
    p.aluno = make_aluno(id=aluno_id)
    p.indicado_por = make_usuario(id=10, nome="Indicador")
    return p


@pytest.fixture
def auth_service():
    svc = AuthService.__new__(AuthService)
    svc.db = MagicMock()
    svc.usuario_repo = MagicMock()
    svc.disciplina_repo = MagicMock()
    svc.diario_aluno_repo = MagicMock()
    svc.aluno_repo = MagicMock()
    svc.pendencia_repo = MagicMock()
    svc.suap_service = MagicMock()
    return svc


# ---------------------------------------------------------------------------
# obter_alunos_ativos
# ---------------------------------------------------------------------------

class TestObterAlunosAtivos:
    def test_retorna_alunos_ativos(self, auth_service):
        auth_service.aluno_repo.listar_por_status.return_value = [make_aluno(status="ativo")]
        result = auth_service.obter_alunos_ativos()
        auth_service.aluno_repo.listar_por_status.assert_called_once_with("ativo")
        assert len(result) == 1

    def test_retorna_lista_vazia(self, auth_service):
        auth_service.aluno_repo.listar_por_status.return_value = []
        result = auth_service.obter_alunos_ativos()
        assert result == []


# ---------------------------------------------------------------------------
# buscar_alunos
# ---------------------------------------------------------------------------

class TestBuscarAlunos:
    def test_busca_por_nome(self, auth_service):
        auth_service.aluno_repo.buscar_por_nome_ou_matricula.return_value = [make_aluno()]
        result = auth_service.buscar_alunos("João")
        auth_service.aluno_repo.buscar_por_nome_ou_matricula.assert_called_once_with("João")

    def test_busca_vazia_retorna_vazio(self, auth_service):
        auth_service.aluno_repo.buscar_por_nome_ou_matricula.return_value = []
        result = auth_service.buscar_alunos("xyz")
        assert result == []


# ---------------------------------------------------------------------------
# validar_pendencia (used by equipe router)
# ---------------------------------------------------------------------------

class TestValidarPendenciaEquipe:
    def test_validar_com_sucesso(self, auth_service):
        pendencia = make_pendencia()
        auth_service.pendencia_repo.get_by_id.return_value = pendencia
        auth_service.pendencia_repo.update.return_value = pendencia
        aluno = make_aluno(status="aguardando_indicacao")
        auth_service.aluno_repo.get_by_id.return_value = aluno

        result = auth_service.validar_pendencia(1, validado_por_id=10, acao="validado")

        auth_service.pendencia_repo.update.assert_called_once()
        assert aluno.status_acompanhamento == "ativo"

    def test_rejeitar_altera_status(self, auth_service):
        pendencia = make_pendencia()
        auth_service.pendencia_repo.get_by_id.return_value = pendencia
        auth_service.pendencia_repo.update.return_value = pendencia
        aluno = make_aluno(status="aguardando_indicacao")
        auth_service.aluno_repo.get_by_id.return_value = aluno

        result = auth_service.validar_pendencia(1, validado_por_id=10, acao="rejeitado")

        assert aluno.status_acompanhamento == "rejeitado"

    def test_acao_invalida_nao_altera_aluno(self, auth_service):
        pendencia = make_pendencia()
        auth_service.pendencia_repo.get_by_id.return_value = pendencia
        auth_service.pendencia_repo.update.return_value = pendencia
        aluno = make_aluno(status="aguardando_indicacao")
        auth_service.aluno_repo.get_by_id.return_value = aluno

        auth_service.validar_pendencia(1, validado_por_id=10, acao="outro")

        assert aluno.status_acompanhamento == "aguardando_indicacao"


# ---------------------------------------------------------------------------
# obter_pendencias (used by equipe router)
# ---------------------------------------------------------------------------

class TestObterPendenciasEquipe:
    def test_lista_pendencias(self, auth_service):
        p = make_pendencia()
        auth_service.pendencia_repo.listar_pendentes.return_value = [p]
        result = auth_service.obter_pendencias()
        assert len(result) == 1
        assert result[0].aluno.nome == "João"

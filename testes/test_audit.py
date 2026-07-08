from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from backend.models.audit_log import AuditLog
from backend.models.usuario import Usuario
from backend.services.audit_service import AuditService
from backend.repositories.audit_log import AuditLogRepository


def make_usuario(id: int = 1, nome: str = "Maria", tipo_perfil: str = "psicopedagogo") -> Usuario:
    u = Usuario()
    u.id = id
    u.nome = nome
    u.email = "maria@escola.edu.br"
    u.tipo_perfil = tipo_perfil
    u.suap_id = "00001"
    u.criado_em = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return u


def make_audit_log(
    id: int = 1,
    usuario_id: int = 1,
    acao: str = "leitura",
    recurso_tipo: str = "perfil_aluno",
    recurso_id: int = 1,
    aluno_id: int = 10,
    ip_origem: str = "127.0.0.1",
) -> AuditLog:
    log = AuditLog()
    log.id = id
    log.usuario_id = usuario_id
    log.acao = acao
    log.recurso_tipo = recurso_tipo
    log.recurso_id = recurso_id
    log.aluno_id = aluno_id
    log.ip_origem = ip_origem
    log.criado_em = datetime(2026, 1, 1, tzinfo=timezone.utc)
    log.usuario = make_usuario(id=usuario_id)
    log.aluno = None
    return log


class TestAuditServiceRegistrar:
    def test_registrar_leitura_perfil(self):
        db = MagicMock()
        service = AuditService(db)
        service.registrar(
            usuario_id=1,
            acao="leitura",
            recurso_tipo="perfil_aluno",
            recurso_id=5,
            aluno_id=10,
            ip_origem="127.0.0.1",
        )
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_registrar_criacao_observacao(self):
        db = MagicMock()
        service = AuditService(db)
        service.registrar(
            usuario_id=2,
            acao="criacao",
            recurso_tipo="observacao_acomodacao",
            recurso_id=3,
            aluno_id=10,
            detalhes="disciplina_id=7",
            ip_origem="10.0.0.1",
        )
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_registrar_falha_nao_propaga_excecao(self):
        db = MagicMock()
        db.commit.side_effect = Exception("DB error")
        service = AuditService(db)
        service.registrar(
            usuario_id=1,
            acao="leitura",
            recurso_tipo="perfil_aluno",
            recurso_id=1,
            aluno_id=10,
        )
        # Should not raise


class TestAuditLogRepositoryListarPorAluno:
    def test_listar_por_aluno_retorna_logs(self):
        db = MagicMock()
        log1 = make_audit_log(id=1, aluno_id=10, acao="leitura")
        log2 = make_audit_log(id=2, aluno_id=10, acao="criacao")
        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = [log1, log2]
        db.execute.return_value = mock_result
        repo = AuditLogRepository(db)
        logs = repo.listar_por_aluno(10, skip=0, limit=50)
        assert len(logs) == 2

    def test_listar_por_aluno_vazio(self):
        db = MagicMock()
        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result
        repo = AuditLogRepository(db)
        logs = repo.listar_por_aluno(999)
        assert len(logs) == 0


class TestAuditLogRepositoryListarFiltrado:
    def test_listar_filtrado_por_recurso_tipo(self):
        db = MagicMock()
        log1 = make_audit_log(recurso_tipo="perfil_aluno")
        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = [log1]
        db.execute.return_value = mock_result
        repo = AuditLogRepository(db)
        logs = repo.listar_filtrado(recurso_tipo="perfil_aluno")
        assert len(logs) == 1

    def test_listar_filtrado_por_acao(self):
        db = MagicMock()
        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result
        repo = AuditLogRepository(db)
        logs = repo.listar_filtrado(acao="exclusao")
        assert len(logs) == 0


class TestAuditLogResponse:
    def test_model_validate_from_log(self):
        log = make_audit_log()
        from backend.schemas.audit_log import AuditLogResponse
        resp = AuditLogResponse.model_validate(log)
        assert resp.acao == "leitura"
        assert resp.recurso_tipo == "perfil_aluno"
        assert resp.recurso_id == 1
        assert resp.aluno_id == 10
        assert resp.ip_origem == "127.0.0.1"

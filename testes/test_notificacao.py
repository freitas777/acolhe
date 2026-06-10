from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from backend.models.notificacao import Notificacao
from backend.models.aluno import Aluno
from backend.models.usuario import Usuario
from backend.services.notificacao_service import NotificacaoService
from backend.schemas.notificacao import NotificacaoResponse, NotificacaoCountResponse


def make_notificacao(
    id: int = 1,
    tipo: str = "aluno_importado",
    titulo: str = "Aluno importado: Joao",
    destino_tipo: str = "napne",
    destino_id: int | None = None,
    aluno_id: int | None = 1,
    lida: bool = False,
) -> Notificacao:
    n = Notificacao()
    n.id = id
    n.tipo = tipo
    n.titulo = titulo
    n.mensagem = "Teste de notificacao"
    n.remetente_id = 10
    n.aluno_id = aluno_id
    n.destino_tipo = destino_tipo
    n.destino_id = destino_id
    n.lida = lida
    n.criada_em = datetime(2024, 1, 1, tzinfo=timezone.utc)
    n.aluno = make_aluno(id=aluno_id) if aluno_id else None
    n.remetente = None
    return n


def make_aluno(id: int = 1, nome: str = "Joao") -> Aluno:
    a = Aluno()
    a.id = id
    a.nome = nome
    return a


def make_usuario(id: int = 1, nome: str = "Maria", tipo_perfil: str = "psicopedagogo") -> Usuario:
    u = Usuario()
    u.id = id
    u.nome = nome
    u.email = "maria@escola.edu.br"
    u.tipo_perfil = tipo_perfil
    u.suap_id = "00001"
    u.campus = "Campus Central"
    u.criado_em = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return u


@pytest.fixture
def notificacao_service():
    svc = NotificacaoService.__new__(NotificacaoService)
    svc.db = MagicMock()
    svc.repo = MagicMock()
    return svc


class TestNotificacaoServiceListar:
    def test_listar_napne(self, notificacao_service):
        n = make_notificacao()
        notificacao_service.repo.listar_por_destino.return_value = [n]
        result = notificacao_service.listar(
            destino_tipo="napne", campus="Campus Central", usuario_id=1, skip=0, limit=20
        )
        notificacao_service.repo.listar_por_destino.assert_called_once_with(
            destino_tipo="napne", destino_id=None, campus="Campus Central",
            usuario_id=1, skip=0, limit=20
        )
        assert len(result) == 1
        assert result[0].tipo == "aluno_importado"

    def test_listar_professor(self, notificacao_service):
        n = make_notificacao(destino_tipo="professor", destino_id=5)
        notificacao_service.repo.listar_por_destino.return_value = [n]
        result = notificacao_service.listar(
            destino_tipo="professor", destino_id=5, usuario_id=5
        )
        notificacao_service.repo.listar_por_destino.assert_called_once_with(
            destino_tipo="professor", destino_id=5, campus=None,
            usuario_id=5, skip=0, limit=20
        )
        assert len(result) == 1


class TestNotificacaoServiceContar:
    def test_contar_nao_lidas_napne(self, notificacao_service):
        notificacao_service.repo.contar_nao_lidas.return_value = 3
        result = notificacao_service.contar_nao_lidas(
            destino_tipo="napne", campus="Campus Central", usuario_id=1
        )
        notificacao_service.repo.contar_nao_lidas.assert_called_once_with(
            destino_tipo="napne", destino_id=None, campus="Campus Central", usuario_id=1
        )
        assert result == 3

    def test_contar_nao_lidas_usuario(self, notificacao_service):
        notificacao_service.repo.contar_nao_lidas.return_value = 0
        result = notificacao_service.contar_nao_lidas(
            destino_tipo="usuario", destino_id=5, usuario_id=5
        )
        assert result == 0


class TestNotificacaoServiceMarcar:
    def test_marcar_como_lida(self, notificacao_service):
        notificacao_service.repo.marcar_como_lida.return_value = True
        result = notificacao_service.marcar_como_lida(1, usuario_id=1)
        assert result is True
        notificacao_service.repo.marcar_como_lida.assert_called_once_with(1, 1)

    def test_marcar_como_lida_nao_encontrada(self, notificacao_service):
        notificacao_service.repo.marcar_como_lida.return_value = False
        result = notificacao_service.marcar_como_lida(999, usuario_id=1)
        assert result is False

    def test_marcar_todas_como_lidas(self, notificacao_service):
        notificacao_service.repo.marcar_todas_como_lidas.return_value = 5
        result = notificacao_service.marcar_todas_como_lidas(
            destino_tipo="napne", campus="Campus Central", usuario_id=1
        )
        notificacao_service.repo.marcar_todas_como_lidas.assert_called_once_with(
            destino_tipo="napne", destino_id=None, campus="Campus Central", usuario_id=1
        )
        assert result == 5


class TestNotificacaoServiceEstaLida:
    def test_esta_lida_true(self, notificacao_service):
        notificacao_service.repo.esta_lida.return_value = True
        result = notificacao_service.esta_lida(1, usuario_id=1)
        assert result is True
        notificacao_service.repo.esta_lida.assert_called_once_with(1, 1)

    def test_esta_lida_false(self, notificacao_service):
        notificacao_service.repo.esta_lida.return_value = False
        result = notificacao_service.esta_lida(1, usuario_id=2)
        assert result is False


class TestNotificacaoServiceExcluir:
    def test_excluir_sucesso(self, notificacao_service):
        notificacao_service.repo.excluir.return_value = True
        result = notificacao_service.excluir(1, usuario_id=1)
        assert result is True
        notificacao_service.repo.excluir.assert_called_once_with(1, 1)

    def test_excluir_nao_encontrada(self, notificacao_service):
        notificacao_service.repo.excluir.return_value = False
        result = notificacao_service.excluir(999, usuario_id=1)
        assert result is False


class TestNotificacaoServiceCriar:
    def test_criar_notificacao_aluno_importado(self, notificacao_service):
        n = make_notificacao()
        notificacao_service.repo.create.return_value = n
        result = notificacao_service.criar_notificacao(
            tipo="aluno_importado",
            titulo="Aluno importado: Joao",
            mensagem="O aluno Joao foi importado.",
            remetente_id=10,
            aluno_id=1,
            destino_tipo="napne",
        )
        notificacao_service.repo.create.assert_called_once_with({
            "tipo": "aluno_importado",
            "titulo": "Aluno importado: Joao",
            "mensagem": "O aluno Joao foi importado.",
            "remetente_id": 10,
            "aluno_id": 1,
            "destino_tipo": "napne",
            "destino_id": None,
        })
        assert result.tipo == "aluno_importado"

    def test_criar_notificacao_assistido_na_turma(self, notificacao_service):
        n = make_notificacao(
            tipo="assistido_na_turma",
            titulo="Aluno assistido na sua turma: Maria",
            destino_tipo="professor",
            destino_id=5,
        )
        notificacao_service.repo.create.return_value = n
        result = notificacao_service.criar_notificacao(
            tipo="assistido_na_turma",
            titulo="Aluno assistido na sua turma: Maria",
            mensagem="O aluno assistido Maria esta matriculado na disciplina Matematica.",
            aluno_id=2,
            destino_tipo="professor",
            destino_id=5,
        )
        notificacao_service.repo.create.assert_called_once()
        assert result.tipo == "assistido_na_turma"
        assert result.destino_tipo == "professor"


class TestNotificacaoResponse:
    def test_model_validate(self):
        n = make_notificacao()
        resp = NotificacaoResponse.model_validate(n)
        assert resp.id == 1
        assert resp.tipo == "aluno_importado"
        assert resp.titulo == "Aluno importado: Joao"
        assert resp.lida is False
        assert resp.destino_tipo == "napne"

    def test_aluno_nome_populated(self):
        n = make_notificacao()
        resp = NotificacaoResponse.model_validate(n)
        resp.aluno_nome = n.aluno.nome
        assert resp.aluno_nome == "Joao"

    def test_lida_overridden_per_user(self):
        n = make_notificacao()
        resp = NotificacaoResponse.model_validate(n)
        resp.lida = True
        assert resp.lida is True


class TestNotificacaoCountResponse:
    def test_count_response(self):
        resp = NotificacaoCountResponse(nao_lidas=5)
        assert resp.nao_lidas == 5

    def test_count_zero(self):
        resp = NotificacaoCountResponse(nao_lidas=0)
        assert resp.nao_lidas == 0

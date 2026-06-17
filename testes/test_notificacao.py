from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from backend.models.notificacao import Notificacao
from backend.models.notificacao import NotificacaoLeitura
from backend.models.aluno import Aluno
from backend.models.usuario import Usuario
from backend.services.notificacao_service import NotificacaoService
from backend.repositories.notificacao import NotificacaoRepository
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


# ---------------------------------------------------------------------------
# Repository tests (mock-based)
# ---------------------------------------------------------------------------

@pytest.fixture
def notificacao_repo():
    db = MagicMock()
    repo = NotificacaoRepository.__new__(NotificacaoRepository)
    repo.model = Notificacao
    repo.db = db
    return repo


class TestNotificacaoRepositoryMarcarComoLida:
    def test_notificacao_nao_encontrada(self, notificacao_repo):
        notificacao_repo.get_by_id = MagicMock(return_value=None)
        result = notificacao_repo.marcar_como_lida(999, usuario_id=1)
        assert result is False
        notificacao_repo.db.add.assert_not_called()

    def test_cria_leitura_quando_nao_existe(self, notificacao_repo):
        notificacao_repo.get_by_id = MagicMock(return_value=make_notificacao())
        notificacao_repo.db.get = MagicMock(return_value=None)
        result = notificacao_repo.marcar_como_lida(1, usuario_id=5)
        assert result is True
        notificacao_repo.db.add.assert_called_once()
        notificacao_repo.db.commit.assert_called_once()
        leitura = notificacao_repo.db.add.call_args[0][0]
        assert isinstance(leitura, NotificacaoLeitura)
        assert leitura.notificacao_id == 1
        assert leitura.usuario_id == 5

    def test_nao_cria_leitura_quando_ja_existe(self, notificacao_repo):
        notificacao_repo.get_by_id = MagicMock(return_value=make_notificacao())
        existing = MagicMock()
        notificacao_repo.db.get = MagicMock(return_value=existing)
        result = notificacao_repo.marcar_como_lida(1, usuario_id=5)
        assert result is True
        notificacao_repo.db.add.assert_not_called()


class TestNotificacaoRepositoryEstaLida:
    def test_lida(self, notificacao_repo):
        leitura = MagicMock()
        leitura.excluida = False
        notificacao_repo.db.get = MagicMock(return_value=leitura)
        assert notificacao_repo.esta_lida(1, usuario_id=1) is True

    def test_nao_lida(self, notificacao_repo):
        notificacao_repo.db.get = MagicMock(return_value=None)
        assert notificacao_repo.esta_lida(1, usuario_id=1) is False

    def test_excluida_conta_como_nao_lida(self, notificacao_repo):
        leitura = MagicMock()
        leitura.excluida = True
        notificacao_repo.db.get = MagicMock(return_value=leitura)
        assert notificacao_repo.esta_lida(1, usuario_id=1) is False


class TestNotificacaoRepositoryExcluir:
    def test_notificacao_nao_encontrada(self, notificacao_repo):
        notificacao_repo.get_by_id = MagicMock(return_value=None)
        result = notificacao_repo.excluir(999, usuario_id=1)
        assert result is False

    def test_cria_leitura_excluida(self, notificacao_repo):
        notificacao_repo.get_by_id = MagicMock(return_value=make_notificacao())
        notificacao_repo.db.get = MagicMock(return_value=None)
        result = notificacao_repo.excluir(1, usuario_id=5)
        assert result is True
        notificacao_repo.db.add.assert_called_once()
        leitura = notificacao_repo.db.add.call_args[0][0]
        assert isinstance(leitura, NotificacaoLeitura)
        assert leitura.excluida is True
        assert leitura.notificacao_id == 1
        assert leitura.usuario_id == 5

    def test_atualiza_leitura_existente_para_excluida(self, notificacao_repo):
        notificacao_repo.get_by_id = MagicMock(return_value=make_notificacao())
        existing = MagicMock()
        existing.excluida = False
        notificacao_repo.db.get = MagicMock(return_value=existing)
        result = notificacao_repo.excluir(1, usuario_id=5)
        assert result is True
        assert existing.excluida is True
        notificacao_repo.db.add.assert_not_called()


class TestNotificacaoRepositoryMarcarTodas:
    def test_nenhuma_nao_lida(self, notificacao_repo):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        notificacao_repo.db.execute = MagicMock(return_value=mock_result)
        result = notificacao_repo.marcar_todas_como_lidas(
            destino_tipo="napne", destino_id=None, usuario_id=1,
        )
        assert result == 0
        notificacao_repo.db.add.assert_not_called()

    def test_marca_duas_nao_lidas(self, notificacao_repo):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [10, 20]
        notificacao_repo.db.execute = MagicMock(return_value=mock_result)
        notificacao_repo.db.get = MagicMock(return_value=None)
        result = notificacao_repo.marcar_todas_como_lidas(
            destino_tipo="napne", destino_id=None, usuario_id=1,
        )
        assert result == 2
        assert notificacao_repo.db.add.call_count == 2
        notificacao_repo.db.commit.assert_called_once()

    def test_pula_leitura_ja_existente(self, notificacao_repo):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [10, 20]
        existing_leitura = MagicMock()
        notificacao_repo.db.execute = MagicMock(return_value=mock_result)
        notificacao_repo.db.get = MagicMock(
            side_effect=lambda cls, pk: existing_leitura if pk == (10, 1) else None,
        )
        result = notificacao_repo.marcar_todas_como_lidas(
            destino_tipo="napne", destino_id=None, usuario_id=1,
        )
        assert result == 2
        notificacao_repo.db.add.assert_called_once()

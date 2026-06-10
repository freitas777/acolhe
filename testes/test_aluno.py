from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from backend.models.aluno import Aluno
from backend.models.perfil_aluno import PerfilAluno
from backend.schemas.aluno import AlunoCreate, AlunoUpdate
from backend.schemas.perfil_aluno import PerfilAlunoCreate, PerfilAlunoUpdate
from backend.services.aluno_service import AlunoService


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def make_aluno(id: int = 1, nome: str = "João Silva", observacoes: str | None = None) -> Aluno:
    aluno = Aluno()
    aluno.id = id
    aluno.nome = nome
    aluno.observacoes = observacoes
    aluno.criado_em = datetime(2024, 1, 1)
    aluno.perfil = None
    return aluno


def make_perfil(id: int = 1, aluno_id: int = 1) -> PerfilAluno:
    perfil = PerfilAluno()
    perfil.id = id
    perfil.aluno_id = aluno_id
    perfil.nivel_atencao = None
    perfil.dificuldade_leitura = False
    perfil.preferencia = None
    perfil.interesses = None
    perfil.diagnostico = None
    return perfil


def _mock_query_chain(db, result):
    q = MagicMock()
    db.query.return_value = q
    q.options.return_value = q
    q.filter.return_value = q
    q.offset.return_value = q
    q.limit.return_value = q
    q.first.return_value = result
    q.all.return_value = result if isinstance(result, list) else [result]
    return q


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    svc = AlunoService.__new__(AlunoService)
    svc.db = db
    svc.repo = MagicMock()
    svc.perfil_service = MagicMock()
    return svc


# ---------------------------------------------------------------------------
# criar_aluno
# ---------------------------------------------------------------------------

class TestCriarAluno:
    def test_cria_aluno_com_sucesso(self, service, db):
        aluno = make_aluno()
        db.add.return_value = None
        db.refresh.return_value = None
        db.commit.return_value = None

        def fake_refresh(a):
            a.id = 1
        db.refresh.side_effect = fake_refresh

        data = AlunoCreate(nome="João Silva")
        result = service.criar_aluno(data)

        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_cria_aluno_com_observacoes(self, service, db):
        aluno = make_aluno(observacoes="Tem dislexia")
        db.refresh.side_effect = lambda a: setattr(a, 'id', 1) or None

        data = AlunoCreate(nome="João Silva", observacoes="Tem dislexia")
        result = service.criar_aluno(data)

        db.add.assert_called_once()


# ---------------------------------------------------------------------------
# listar_alunos
# ---------------------------------------------------------------------------

class TestListarAlunos:
    def test_retorna_lista_vazia(self, service, db):
        _mock_query_chain(db, [])
        result = service.listar_alunos()
        assert result == []

    def test_retorna_alunos(self, service, db):
        _mock_query_chain(db, [make_aluno(1, "Ana"), make_aluno(2, "Carlos")])
        result = service.listar_alunos()
        assert len(result) == 2

    def test_repassa_skip_e_limit(self, service, db):
        q = _mock_query_chain(db, [])
        service.listar_alunos(skip=10, limit=5)
        q.offset.assert_called_once_with(10)
        q.limit.assert_called_once_with(5)


# ---------------------------------------------------------------------------
# obter_aluno_por_id
# ---------------------------------------------------------------------------

class TestObterAlunoPorId:
    def test_retorna_aluno_existente(self, service, db):
        aluno = make_aluno(id=1)
        _mock_query_chain(db, aluno)

        result = service.obter_aluno_por_id(1)

        assert result.id == 1

    def test_levanta_erro_quando_nao_encontrado(self, service, db):
        _mock_query_chain(db, None)

        with pytest.raises(ValueError) as exc:
            service.obter_aluno_por_id(99)

        assert "não encontrado" in str(exc.value)


# ---------------------------------------------------------------------------
# atualizar_aluno
# ---------------------------------------------------------------------------

class TestAtualizarAluno:
    def test_atualiza_com_sucesso(self, service, db):
        aluno = make_aluno(nome="João")
        _mock_query_chain(db, aluno)

        data = AlunoUpdate(nome="João Editado")
        result = service.atualizar_aluno(1, data)

        assert aluno.nome == "João Editado"
        db.commit.assert_called_once()

    def test_levanta_erro_quando_nao_encontrado(self, service, db):
        _mock_query_chain(db, None)

        with pytest.raises(ValueError) as exc:
            service.atualizar_aluno(99, AlunoUpdate(nome="X"))

        assert "não encontrado" in str(exc.value)

    def test_atualiza_apenas_campos_enviados(self, service, db):
        aluno = make_aluno()
        _mock_query_chain(db, aluno)

        service.atualizar_aluno(1, AlunoUpdate())

        assert aluno.nome == "João Silva"
        db.commit.assert_called_once()


# ---------------------------------------------------------------------------
# deletar_aluno
# ---------------------------------------------------------------------------

class TestDeletarAluno:
    def test_deleta_com_sucesso(self, service, db):
        aluno = make_aluno()
        _mock_query_chain(db, aluno)

        result = service.deletar_aluno(1)

        assert result is True
        db.delete.assert_called_once_with(aluno)
        db.commit.assert_called_once()

    def test_retorna_false_quando_nao_encontrado(self, service, db):
        _mock_query_chain(db, None)

        result = service.deletar_aluno(99)

        assert result is False


# ---------------------------------------------------------------------------
# criar_perfil (via db.query)
# ---------------------------------------------------------------------------

class TestCriarPerfil:
    def test_cria_perfil_com_sucesso(self, service, db):
        aluno = make_aluno()

        def query_side_effect(model):
            q = MagicMock()
            q.filter.return_value = q
            if model is Aluno:
                q.first.return_value = aluno
            else:
                q.first.return_value = None
            q.options.return_value = q
            q.offset.return_value = q
            q.limit.return_value = q
            q.all.return_value = []
            return q

        db.query.side_effect = query_side_effect

        data = PerfilAlunoCreate()
        result = service.criar_perfil(1, data)

        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_levanta_erro_quando_aluno_nao_encontrado(self, service, db):
        def query_side_effect(model):
            q = MagicMock()
            q.filter.return_value = q
            q.first.return_value = None
            return q

        db.query.side_effect = query_side_effect

        with pytest.raises(ValueError):
            service.criar_perfil(99, PerfilAlunoCreate())


# ---------------------------------------------------------------------------
# atualizar_perfil (via db.query)
# ---------------------------------------------------------------------------

class TestAtualizarPerfil:
    def test_atualiza_perfil_com_sucesso(self, service, db):
        perfil = make_perfil()
        perfil.dificuldade_leitura = False

        def query_side_effect(model):
            q = MagicMock()
            q.filter.return_value = q
            q.first.return_value = perfil
            return q

        db.query.side_effect = query_side_effect

        data = PerfilAlunoUpdate(dificuldade_leitura=True)
        result = service.atualizar_perfil(1, data)

        assert perfil.dificuldade_leitura is True
        db.commit.assert_called_once()

    def test_levanta_erro_quando_perfil_nao_encontrado(self, service, db):
        def query_side_effect(model):
            q = MagicMock()
            q.filter.return_value = q
            q.first.return_value = None
            return q

        db.query.side_effect = query_side_effect

        with pytest.raises(ValueError):
            service.atualizar_perfil(99, PerfilAlunoUpdate())

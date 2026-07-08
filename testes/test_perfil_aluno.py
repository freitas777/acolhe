from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from backend.models.aluno import Aluno
from backend.models.perfil_aluno import PerfilAluno, NivelAtencao, PreferenciaAprendizado
from backend.repositories.perfil_aluno import PerfilAlunoRepository


def make_aluno(id: int = 1) -> Aluno:
    aluno = Aluno()
    aluno.id = id
    aluno.nome = "Aluno Teste"
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


@pytest.fixture
def repo():
    db = MagicMock()
    return PerfilAlunoRepository(db)


class TestGetByAlunoId:
    def test_retorna_perfil_existente(self, repo):
        repo.db.query.return_value.filter.return_value.first.return_value = make_perfil()
        result = repo.get_by_aluno_id(1)
        assert result is not None
        assert result.aluno_id == 1

    def test_retorna_none_quando_nao_encontrado(self, repo):
        repo.db.query.return_value.filter.return_value.first.return_value = None
        result = repo.get_by_aluno_id(99)
        assert result is None


class TestCreate:
    def test_cria_perfil_com_sucesso(self, repo):
        perfil = make_perfil()
        def fake_refresh(instance):
            instance.id = 1
        repo.db.refresh.side_effect = fake_refresh
        result = repo.create({"aluno_id": 1})
        repo.db.add.assert_called_once()
        repo.db.commit.assert_called_once()

    def test_cria_perfil_com_dados_completos(self, repo):
        def fake_refresh(instance):
            instance.id = 1
        repo.db.refresh.side_effect = fake_refresh
        result = repo.create({
            "aluno_id": 1,
            "nivel_atencao": NivelAtencao.alto,
            "dificuldade_leitura": True,
            "preferencia": PreferenciaAprendizado.visual,
            "interesses": "matemática",
            "diagnostico": "TDAH",
        })
        repo.db.add.assert_called_once()


class TestUpdate:
    def test_atualiza_perfil_com_sucesso(self, repo):
        repo.db.get.return_value = make_perfil()
        repo.update(1, {"dificuldade_leitura": True})
        repo.db.commit.assert_called_once()

    def test_retorna_none_quando_perfil_nao_existe(self, repo):
        repo.db.get.return_value = None
        result = repo.update(999, {"dificuldade_leitura": True})
        assert result is None

    def test_atualiza_apenas_campos_enviados(self, repo):
        repo.db.get.return_value = make_perfil()
        repo.update(1, {})
        repo.db.commit.assert_called_once()


class TestDelete:
    def test_deleta_perfil_com_sucesso(self, repo):
        repo.db.get.return_value = make_perfil(id=5)
        result = repo.delete(5)
        assert result is True
        repo.db.delete.assert_called_once()

    def test_retorna_false_quando_nao_encontrado(self, repo):
        repo.db.get.return_value = None
        result = repo.delete(999)
        assert result is False

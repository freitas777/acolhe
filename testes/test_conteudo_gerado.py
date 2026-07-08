from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from backend.models.conteudo_gerado import ConteudoGerado
from backend.models.aluno import Aluno
from backend.repositories.conteudo_gerado import ConteudoGeradoRepository


def make_aluno(id: int = 1) -> Aluno:
    a = Aluno()
    a.id = id
    a.nome = "João"
    return a


def make_conteudo(id: int = 1, aluno_id: int = 1, tema: str = "Fotosíntese") -> ConteudoGerado:
    c = ConteudoGerado()
    c.id = id
    c.aluno_id = aluno_id
    c.usuario_id = None
    c.tema = tema
    c.prompt_utilizado = "prompt"
    c.conteudo = "conteúdo gerado"
    c.modelo_ia = "gemini-pro"
    c.gerado_em = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return c


@pytest.fixture
def repo():
    db = MagicMock()
    return ConteudoGeradoRepository(db)


class TestListByAluno:
    def test_retorna_conteudos_do_aluno(self, repo):
        c1 = make_conteudo(id=1, aluno_id=5)
        c2 = make_conteudo(id=2, aluno_id=5)
        repo.db.query.return_value.filter.return_value.all.return_value = [c1, c2]
        result = repo.list_by_aluno(5)
        assert len(result) == 2
        repo.db.query.assert_called_once_with(ConteudoGerado)

    def test_retorna_lista_vazia_se_sem_conteudos(self, repo):
        repo.db.query.return_value.filter.return_value.all.return_value = []
        result = repo.list_by_aluno(99)
        assert result == []


class TestCreate:
    def test_cria_conteudo_com_sucesso(self, repo):
        novo = make_conteudo()
        repo.db.add.return_value = None
        repo.db.commit.return_value = None
        repo.db.refresh.return_value = None
        repo.db.refresh = MagicMock()
        def fake_refresh(instance):
            instance.id = 1
        repo.db.refresh.side_effect = fake_refresh
        result = repo.create({"aluno_id": 1, "tema": "Teste", "prompt_utilizado": "p", "conteudo": "c", "modelo_ia": "m"})
        repo.db.add.assert_called_once()

    def test_create_chama_commit_e_refresh(self, repo):
        repo.create({"aluno_id": 1, "tema": "X", "prompt_utilizado": "p", "conteudo": "c", "modelo_ia": "m"})
        repo.db.commit.assert_called_once()
        repo.db.refresh.assert_called_once()


class TestGetById:
    def test_retorna_conteudo_existente(self, repo):
        repo.db.get.return_value = make_conteudo()
        result = repo.get_by_id(1)
        assert result is not None
        assert result.tema == "Fotosíntese"

    def test_retorna_none_se_nao_encontrado(self, repo):
        repo.db.get.return_value = None
        result = repo.get_by_id(999)
        assert result is None


class TestUpdate:
    def test_atualiza_conteudo_existente(self, repo):
        repo.db.get.return_value = make_conteudo()
        repo.update(1, {"tema": "Atualizado"})
        repo.db.commit.assert_called_once()

    def test_retorna_none_se_nao_encontrado(self, repo):
        repo.db.get.return_value = None
        result = repo.update(999, {"tema": "X"})
        assert result is None


class TestDelete:
    def test_deleta_conteudo_existente(self, repo):
        repo.db.get.return_value = make_conteudo()
        result = repo.delete(1)
        assert result is True
        repo.db.delete.assert_called_once()

    def test_retorna_false_se_nao_encontrado(self, repo):
        repo.db.get.return_value = None
        result = repo.delete(999)
        assert result is False

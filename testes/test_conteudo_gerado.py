from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from backend.models.conteudo_gerado import ConteudoGerado
from backend.models.aluno import Aluno
from backend.models.usuario import Usuario
from backend.schemas.conteudo_gerado import ConteudoGeradoCreate, ConteudoGeradoUpdate
from backend.services.conteudo_gerado_service import ConteudoGeradoService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_aluno(id: int = 1) -> Aluno:
    a = Aluno()
    a.id = id
    a.nome = "João"
    return a


def make_usuario(id: int = 1) -> Usuario:
    u = Usuario()
    u.id = id
    u.nome = "Maria"
    u.email = "maria@escola.edu.br"
    u.suap_id = "00001"
    u.tipo_perfil = "professor"
    u.criado_em = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return u


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
def service():
    svc = ConteudoGeradoService.__new__(ConteudoGeradoService)
    svc.conteudo_repository = MagicMock()
    svc.aluno_repository = MagicMock()
    svc.usuario_repository = MagicMock()
    return svc


# ---------------------------------------------------------------------------
# criar_conteudo
# ---------------------------------------------------------------------------

class TestCriarConteudo:
    def test_cria_com_sucesso(self, service):
        service.aluno_repository.get_by_id.return_value = make_aluno()
        conteudo = make_conteudo()
        service.conteudo_repository.create.return_value = conteudo

        data = ConteudoGeradoCreate(
            aluno_id=1, tema="Fotosíntese",
            prompt_utilizado="prompt", conteudo="texto", modelo_ia="gemini-pro"
        )
        result = service.criar_conteudo(data)

        service.conteudo_repository.create.assert_called_once()
        assert result.tema == "Fotosíntese"

    def test_levanta_404_aluno_nao_encontrado(self, service):
        service.aluno_repository.get_by_id.return_value = None
        data = ConteudoGeradoCreate(
            aluno_id=99, tema="X",
            prompt_utilizado="p", conteudo="c", modelo_ia="m"
        )
        with pytest.raises(HTTPException) as exc:
            service.criar_conteudo(data)
        assert exc.value.status_code == 404

    def test_levanta_404_usuario_nao_encontrado(self, service):
        service.aluno_repository.get_by_id.return_value = make_aluno()
        service.usuario_repository.get_by_id.return_value = None
        data = ConteudoGeradoCreate(
            aluno_id=1, usuario_id=99, tema="X",
            prompt_utilizado="p", conteudo="c", modelo_ia="m"
        )
        with pytest.raises(HTTPException) as exc:
            service.criar_conteudo(data)
        assert exc.value.status_code == 404

    def test_sem_usuario_id_nao_valida_usuario(self, service):
        service.aluno_repository.get_by_id.return_value = make_aluno()
        service.conteudo_repository.create.return_value = make_conteudo()

        data = ConteudoGeradoCreate(
            aluno_id=1, tema="X",
            prompt_utilizado="p", conteudo="c", modelo_ia="m"
        )
        result = service.criar_conteudo(data)

        service.usuario_repository.get_by_id.assert_not_called()


# ---------------------------------------------------------------------------
# listar_conteudos
# ---------------------------------------------------------------------------

class TestListarConteudos:
    def test_lista_todos_sem_aluno_id(self, service):
        service.conteudo_repository.list_all.return_value = [make_conteudo()]
        result = service.listar_conteudos()
        service.conteudo_repository.list_all.assert_called_once()
        assert len(result) == 1

    def test_lista_por_aluno(self, service):
        service.aluno_repository.get_by_id.return_value = make_aluno()
        service.conteudo_repository.list_by_aluno.return_value = [make_conteudo()]
        result = service.listar_conteudos(aluno_id=1)
        service.conteudo_repository.list_by_aluno.assert_called_once_with(1)

    def test_levanta_404_aluno_nao_encontrado(self, service):
        service.aluno_repository.get_by_id.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.listar_conteudos(aluno_id=99)
        assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# obter_conteudo_por_id
# ---------------------------------------------------------------------------

class TestObterConteudoPorId:
    def test_retorna_conteudo_existente(self, service):
        service.conteudo_repository.get_by_id.return_value = make_conteudo()
        result = service.obter_conteudo_por_id(1)
        assert result.tema == "Fotosíntese"

    def test_levanta_404_nao_encontrado(self, service):
        service.conteudo_repository.get_by_id.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.obter_conteudo_por_id(99)
        assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# atualizar_conteudo
# ---------------------------------------------------------------------------

class TestAtualizarConteudo:
    def test_atualiza_com_sucesso(self, service):
        service.conteudo_repository.get_by_id.return_value = make_conteudo()
        service.conteudo_repository.update.return_value = make_conteudo(tema="Atualizado")

        data = ConteudoGeradoUpdate(tema="Atualizado")
        result = service.atualizar_conteudo(1, data)

        service.conteudo_repository.update.assert_called_once()

    def test_levanta_404_nao_encontrado(self, service):
        service.conteudo_repository.get_by_id.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.atualizar_conteudo(99, ConteudoGeradoUpdate(tema="X"))
        assert exc.value.status_code == 404

    def test_atualiza_apenas_campos_enviados(self, service):
        service.conteudo_repository.get_by_id.return_value = make_conteudo()
        service.conteudo_repository.update.return_value = make_conteudo()

        service.atualizar_conteudo(1, ConteudoGeradoUpdate())

        service.conteudo_repository.update.assert_called_once_with(1, {})


# ---------------------------------------------------------------------------
# deletar_conteudo
# ---------------------------------------------------------------------------

class TestDeletarConteudo:
    def test_deleta_com_sucesso(self, service):
        service.conteudo_repository.get_by_id.return_value = make_conteudo()
        service.deletar_conteudo(1)
        service.conteudo_repository.delete.assert_called_once_with(1)

    def test_levanta_404_nao_encontrado(self, service):
        service.conteudo_repository.get_by_id.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.deletar_conteudo(99)
        assert exc.value.status_code == 404

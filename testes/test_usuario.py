from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from backend.models.usuario import Usuario
from backend.schemas.usuario import UsuarioCreate, UsuarioUpdate
from backend.services.usuario_service import UsuarioService


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def make_usuario(
    id: int = 1, suap_id: str = "00001", nome: str = "Maria Professora", email: str = "maria@escola.edu.br", tipo_perfil: str = "professor",
) -> Usuario:
    u = Usuario()
    u.id = id
    u.suap_id = suap_id
    u.nome = nome
    u.email = email
    u.tipo_perfil = tipo_perfil
    u.criado_em = datetime(2024, 1, 1)
    return u


@pytest.fixture
def service():
    svc = UsuarioService.__new__(UsuarioService)
    svc.repository = MagicMock()
    return svc


# ---------------------------------------------------------------------------
# criar_usuario
# ---------------------------------------------------------------------------

class TestCriarUsuario:
    def _data(
        self,
        suap_id: str = "00001",
        nome: str = "Maria Professora",
        email: str = "maria@escola.edu.br",
        tipo_perfil: str = "professor",
    ):
        return UsuarioCreate(
            suap_id=suap_id,
            nome=nome,
            email=email,
            tipo_perfil=tipo_perfil,
        )

    def test_cria_usuario_com_sucesso(self, service):
        service.repository.get_by_suap_id.return_value = None
        service.repository.create.return_value = make_usuario()

        result = service.criar_usuario(self._data())

        assert result.id == 1
        assert result.suap_id == "00001"
        service.repository.create.assert_called_once()

    def test_levanta_400_quando_suap_id_duplicado(self, service):
        service.repository.get_by_suap_id.return_value = make_usuario()

        with pytest.raises(HTTPException) as exc:
            service.criar_usuario(self._data())

        assert exc.value.status_code == 400
        assert "SUAP ID" in exc.value.detail
        service.repository.create.assert_not_called()

    def test_tipo_perfil_default_professor(self, service):
        service.repository.get_by_suap_id.return_value = None
        usuario = make_usuario()
        service.repository.create.return_value = usuario

        service.criar_usuario(self._data())

        payload = service.repository.create.call_args[0][0]
        assert payload["tipo_perfil"] == "professor"

    def test_cria_usuario_como_psicopedagogo(self, service):
        service.repository.get_by_suap_id.return_value = None
        usuario = make_usuario(tipo_perfil="psicopedagogo")
        service.repository.create.return_value = usuario

        result = service.criar_usuario(self._data(tipo_perfil="psicopedagogo"))

        assert result.tipo_perfil == "psicopedagogo"


# ---------------------------------------------------------------------------
# listar_usuarios
# ---------------------------------------------------------------------------

class TestListarUsuarios:
    def test_retorna_lista_vazia(self, service):
        service.repository.list_all.return_value = []
        result = service.listar_usuarios()
        assert result == []

    def test_retorna_lista_com_usuarios(self, service):
        service.repository.list_all.return_value = [
            make_usuario(1, "00001"),
            make_usuario(2, "00002"),
        ]
        result = service.listar_usuarios()
        assert len(result) == 2

    def test_repassa_skip_e_limit(self, service):
        service.repository.list_all.return_value = []
        service.listar_usuarios(skip=10, limit=20)
        service.repository.list_all.assert_called_once_with(skip=10, limit=20)


# ---------------------------------------------------------------------------
# obter_usuario_por_id
# ---------------------------------------------------------------------------

class TestObterUsuarioPorId:
    def test_retorna_usuario_existente(self, service):
        service.repository.get_by_id.return_value = make_usuario()

        result = service.obter_usuario_por_id(1)

        assert result.id == 1

    def test_levanta_404_quando_nao_encontrado(self, service):
        service.repository.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            service.obter_usuario_por_id(99)

        assert exc.value.status_code == 404
        assert "Usuário" in exc.value.detail


# ---------------------------------------------------------------------------
# atualizar_usuario
# ---------------------------------------------------------------------------

class TestAtualizarUsuario:
    def test_atualiza_com_sucesso(self, service):
        usuario_original = make_usuario()
        usuario_atualizado = make_usuario(nome="Maria Editada")
        service.repository.get_by_id.return_value = usuario_original
        service.repository.update.return_value = usuario_atualizado

        result = service.atualizar_usuario(1, UsuarioUpdate(nome="Maria Editada"))

        assert result.nome == "Maria Editada"
        service.repository.update.assert_called_once_with(1, {"nome": "Maria Editada"})

    def test_levanta_404_quando_usuario_nao_existe(self, service):
        service.repository.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            service.atualizar_usuario(99, UsuarioUpdate(nome="X"))

        assert exc.value.status_code == 404

    def test_levanta_404_quando_update_retorna_none(self, service):
        service.repository.get_by_id.return_value = make_usuario()
        service.repository.update.return_value = None

        with pytest.raises(HTTPException) as exc:
            service.atualizar_usuario(1, UsuarioUpdate(nome="X"))

        assert exc.value.status_code == 404

    def test_atualiza_apenas_campos_enviados(self, service):
        service.repository.get_by_id.return_value = make_usuario()
        service.repository.update.return_value = make_usuario()

        service.atualizar_usuario(1, UsuarioUpdate())

        service.repository.update.assert_called_once_with(1, {})


# ---------------------------------------------------------------------------
# deletar_usuario
# ---------------------------------------------------------------------------

class TestDeletarUsuario:
    def test_deleta_com_sucesso(self, service):
        service.repository.get_by_id.return_value = make_usuario()
        service.repository.delete.return_value = True

        service.deletar_usuario(1)

        service.repository.delete.assert_called_once_with(1)

    def test_levanta_404_quando_nao_encontrado(self, service):
        service.repository.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            service.deletar_usuario(99)

        assert exc.value.status_code == 404

    def test_levanta_500_quando_delete_retorna_false(self, service):
        service.repository.get_by_id.return_value = make_usuario()
        service.repository.delete.return_value = False

        with pytest.raises(HTTPException) as exc:
            service.deletar_usuario(1)

        assert exc.value.status_code == 500


# ---------------------------------------------------------------------------
# obter_usuarios_por_perfil
# ---------------------------------------------------------------------------

class TestObterUsuariosPorPerfil:
    def test_retorna_usuarios_do_perfil(self, service):
        service.repository.filter_by_profile.return_value = [
            make_usuario(tipo_perfil="psicopedagogo"),
        ]

        result = service.obter_usuarios_por_perfil("psicopedagogo")

        service.repository.filter_by_profile.assert_called_once_with("psicopedagogo")
        assert len(result) == 1

    def test_retorna_lista_vazia_quando_sem_usuarios_do_perfil(self, service):
        service.repository.filter_by_profile.return_value = []

        result = service.obter_usuarios_por_perfil("admin")

        assert result == []
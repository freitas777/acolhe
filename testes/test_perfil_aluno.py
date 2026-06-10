from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from backend.models.aluno import Aluno
from backend.models.perfil_aluno import PerfilAluno, NivelAtencao, PreferenciaAprendizado
from backend.schemas.perfil_aluno import PerfilAlunoCreate, PerfilAlunoUpdate
from backend.services.perfil_aluno_service import PerfilAlunoService


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

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
def service():
    svc = PerfilAlunoService.__new__(PerfilAlunoService)
    svc.perfil_repository = MagicMock()
    svc.aluno_repository = MagicMock()
    return svc


# ---------------------------------------------------------------------------
# criar_perfil
# ---------------------------------------------------------------------------

class TestCriarPerfil:
    def test_cria_perfil_com_sucesso(self, service):
        service.aluno_repository.get_by_id.return_value = make_aluno()
        service.perfil_repository.get_by_aluno_id.return_value = None
        perfil = make_perfil()
        service.perfil_repository.create.return_value = perfil

        data = PerfilAlunoCreate()
        result = service.criar_perfil(1, data)

        assert result.aluno_id == 1
        service.perfil_repository.create.assert_called_once()

    def test_levanta_404_quando_aluno_nao_existe(self, service):
        service.aluno_repository.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            service.criar_perfil(99, PerfilAlunoCreate())

        assert exc.value.status_code == 404
        assert "Aluno" in exc.value.detail

    def test_levanta_409_quando_perfil_ja_existe(self, service):
        service.aluno_repository.get_by_id.return_value = make_aluno()
        service.perfil_repository.get_by_aluno_id.return_value = make_perfil()

        with pytest.raises(HTTPException) as exc:
            service.criar_perfil(1, PerfilAlunoCreate())

        assert exc.value.status_code == 409
        assert "Perfil já existe" in exc.value.detail

    def test_inclui_aluno_id_no_payload(self, service):
        service.aluno_repository.get_by_id.return_value = make_aluno()
        service.perfil_repository.get_by_aluno_id.return_value = None
        service.perfil_repository.create.return_value = make_perfil()

        service.criar_perfil(1, PerfilAlunoCreate())

        call_kwargs = service.perfil_repository.create.call_args[0][0]
        assert call_kwargs["aluno_id"] == 1

    def test_cria_perfil_com_dados_completos(self, service):
        service.aluno_repository.get_by_id.return_value = make_aluno()
        service.perfil_repository.get_by_aluno_id.return_value = None

        perfil = make_perfil()
        perfil.nivel_atencao = NivelAtencao.alto
        perfil.dificuldade_leitura = True
        perfil.preferencia = PreferenciaAprendizado.visual
        perfil.interesses = "matemática"
        perfil.diagnostico = "TDAH"
        service.perfil_repository.create.return_value = perfil

        data = PerfilAlunoCreate(
            nivel_atencao=NivelAtencao.alto,
            dificuldade_leitura=True,
            preferencia=PreferenciaAprendizado.visual,
            interesses="matemática",
            diagnostico="TDAH",
        )
        result = service.criar_perfil(1, data)

        assert result.nivel_atencao == NivelAtencao.alto
        assert result.dificuldade_leitura is True
        assert result.diagnostico == "TDAH"


# ---------------------------------------------------------------------------
# obter_perfil_por_aluno
# ---------------------------------------------------------------------------

class TestObterPerfilPorAluno:
    def test_retorna_perfil_existente(self, service):
        service.perfil_repository.get_by_aluno_id.return_value = make_perfil()

        result = service.obter_perfil_por_aluno(1)

        assert result.aluno_id == 1

    def test_levanta_404_quando_nao_encontrado(self, service):
        service.perfil_repository.get_by_aluno_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            service.obter_perfil_por_aluno(99)

        assert exc.value.status_code == 404
        assert "Perfil" in exc.value.detail


# ---------------------------------------------------------------------------
# atualizar_perfil
# ---------------------------------------------------------------------------

class TestAtualizarPerfil:
    def test_atualiza_com_sucesso(self, service):
        perfil_original = make_perfil()
        perfil_atualizado = make_perfil()
        perfil_atualizado.dificuldade_leitura = True
        service.perfil_repository.get_by_aluno_id.return_value = perfil_original
        service.perfil_repository.update.return_value = perfil_atualizado

        data = PerfilAlunoUpdate(dificuldade_leitura=True)
        result = service.atualizar_perfil(1, data)

        assert result.dificuldade_leitura is True
        service.perfil_repository.update.assert_called_once_with(1, {"dificuldade_leitura": True})

    def test_levanta_404_quando_perfil_nao_existe(self, service):
        service.perfil_repository.get_by_aluno_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            service.atualizar_perfil(99, PerfilAlunoUpdate())

        assert exc.value.status_code == 404

    def test_atualiza_apenas_campos_enviados(self, service):
        service.perfil_repository.get_by_aluno_id.return_value = make_perfil()
        service.perfil_repository.update.return_value = make_perfil()

        data = PerfilAlunoUpdate()  # nenhum campo
        service.atualizar_perfil(1, data)

        service.perfil_repository.update.assert_called_once_with(1, {})


# ---------------------------------------------------------------------------
# deletar_perfil
# ---------------------------------------------------------------------------

class TestDeletarPerfil:
    def test_deleta_com_sucesso(self, service):
        service.perfil_repository.get_by_aluno_id.return_value = make_perfil(id=5)
        service.perfil_repository.delete.return_value = True

        service.deletar_perfil(1)

        service.perfil_repository.delete.assert_called_once_with(5)

    def test_levanta_404_quando_nao_encontrado(self, service):
        service.perfil_repository.get_by_aluno_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            service.deletar_perfil(99)

        assert exc.value.status_code == 404

    def test_levanta_500_quando_falha_ao_deletar(self, service):
        service.perfil_repository.get_by_aluno_id.return_value = make_perfil()
        service.perfil_repository.delete.return_value = False

        with pytest.raises(HTTPException) as exc:
            service.deletar_perfil(1)

        assert exc.value.status_code == 500
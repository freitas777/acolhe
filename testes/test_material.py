from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile

from backend.models.material import Material
from backend.schemas.material import MaterialResponse
from backend.services.material_service import MaterialService, _validate_file, _get_extension


def make_material(
    id: int = 1,
    disciplina_id: int = 1,
    usuario_id: int = 1,
    nome_original: str = "apostila.pdf",
    nome_arquivo: str = "abc123.pdf",
    tipo_arquivo: str = "application/pdf",
    tamanho: int = 1024,
    descricao: str | None = None,
    categoria: str = "outro",
) -> Material:
    from datetime import datetime, timezone
    m = Material()
    m.id = id
    m.disciplina_id = disciplina_id
    m.usuario_id = usuario_id
    m.nome_original = nome_original
    m.nome_arquivo = nome_arquivo
    m.tipo_arquivo = tipo_arquivo
    m.tamanho = tamanho
    m.descricao = descricao
    m.categoria = categoria
    m.criado_em = datetime.now(timezone.utc)
    m.usuario = MagicMock(nome="Professor Teste")
    return m


@pytest.fixture
def service():
    svc = MaterialService.__new__(MaterialService)
    svc.repo = MagicMock()
    svc.db = MagicMock()
    svc.diario_aluno_repo = MagicMock()
    svc.aluno_repo = MagicMock()
    svc.usuario_repo = MagicMock()
    return svc


class TestGetExtension:
    def test_pdf(self):
        assert _get_extension("file.pdf") == "pdf"

    def test_docx(self):
        assert _get_extension("document.docx") == "docx"

    def test_no_extension(self):
        assert _get_extension("noext") == ""

    def test_uppercase(self):
        assert _get_extension("FILE.PDF") == "pdf"


class TestValidateFile:
    def test_valid_pdf(self):
        _validate_file("test.pdf", "application/pdf", 1000, b"%PDF-1.4")

    def test_invalid_extension(self):
        with pytest.raises(HTTPException) as exc:
            _validate_file("test.exe", "application/exe", 1000, b"fake")
        assert exc.value.status_code == 400

    def test_file_too_large(self):
        with pytest.raises(HTTPException) as exc:
            _validate_file("test.pdf", "application/pdf", 20 * 1024 * 1024, b"%PDF-1.4")
        assert exc.value.status_code == 400

    def test_valid_extensions(self):
        magic_bytes = {
            "pdf": b"%PDF-1.4",
            "doc": b"\xd0\xcf\x11\xe0",
            "docx": b"PK\x03\x04",
            "ppt": b"\xd0\xcf\x11\xe0",
            "pptx": b"PK\x03\x04",
            "png": b"\x89PNG",
            "jpg": b"\xff\xd8\xff",
            "jpeg": b"\xff\xd8\xff",
            "txt": b"qualquer texto",
        }
        for ext in ["pdf", "doc", "docx", "ppt", "pptx", "png", "jpg", "jpeg", "txt"]:
            _validate_file(f"test.{ext}", "application/octet-stream", 1000, magic_bytes[ext])


class TestListarMateriais:
    def test_retorna_lista(self, service):
        mat = make_material()
        service.repo.listar_por_disciplina.return_value = [mat]
        result = service.listar_materiais(1)
        assert len(result) == 1
        assert result[0].nome_original == "apostila.pdf"
        assert result[0].usuario_nome == "Professor Teste"

    def test_lista_vazia(self, service):
        service.repo.listar_por_disciplina.return_value = []
        result = service.listar_materiais(1)
        assert result == []

    def test_lista_com_categoria(self, service):
        mat = make_material()
        mat.categoria = "prova"
        service.repo.listar_por_disciplina.return_value = [mat]
        result = service.listar_materiais(1, categoria="prova")
        assert len(result) == 1


class TestUploadMaterial:
    @pytest.mark.asyncio
    async def test_upload_sucesso(self, service):
        mat = make_material()
        service.repo.create.return_value = mat
        file = UploadFile(filename="test.pdf", file=MagicMock())
        file.read = AsyncMock(return_value=b"%PDF-1.4 fake content")
        with patch("backend.services.material_service._get_upload_dir") as mock_dir:
            tmp = Path(tempfile.mkdtemp())
            mock_dir.return_value = tmp
            result = await service.upload_material(
                disciplina_id=1, usuario_id=1, file=file, descricao="Teste"
            )
        assert result.nome_original == "apostila.pdf"
        service.repo.create.assert_called_once()
        create_data = service.repo.create.call_args[0][0]
        assert create_data["disciplina_id"] == 1
        assert create_data["usuario_id"] == 1
        assert create_data["descricao"] == "Teste"

    @pytest.mark.asyncio
    async def test_upload_extensao_invalida(self, service):
        file = UploadFile(filename="virus.exe", file=MagicMock())
        file.read = AsyncMock(return_value=b"fake")
        with pytest.raises(HTTPException) as exc:
            await service.upload_material(disciplina_id=1, usuario_id=1, file=file)
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_arquivo_grande(self, service):
        file = UploadFile(filename="big.pdf", file=MagicMock())
        file.read = AsyncMock(return_value=b"x" * (20 * 1024 * 1024))
        with pytest.raises(HTTPException) as exc:
            await service.upload_material(disciplina_id=1, usuario_id=1, file=file)
        assert exc.value.status_code == 400


class TestDeletarMaterial:
    def test_dono_pode_deletar(self, service):
        mat = make_material(usuario_id=1)
        service.repo.get_by_id.return_value = mat
        with patch("backend.services.material_service._get_upload_dir") as mock_dir:
            tmp = Path(tempfile.mkdtemp())
            mock_dir.return_value = tmp
            result = service.deletar_material(1, usuario_id=1, tipo_perfil="professor")
        assert result is True

    def test_nao_dono_nao_pode_deletar(self, service):
        mat = make_material(usuario_id=2)
        service.repo.get_by_id.return_value = mat
        with pytest.raises(HTTPException) as exc:
            service.deletar_material(1, usuario_id=1, tipo_perfil="professor")
        assert exc.value.status_code == 403

    def test_admin_pode_deletar_de_qualquer_um(self, service):
        mat = make_material(usuario_id=2)
        service.repo.get_by_id.return_value = mat
        with patch("backend.services.material_service._get_upload_dir") as mock_dir:
            tmp = Path(tempfile.mkdtemp())
            mock_dir.return_value = tmp
            result = service.deletar_material(1, usuario_id=1, tipo_perfil="admin")
        assert result is True

    def test_404_quando_nao_encontrado(self, service):
        service.repo.get_by_id.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.deletar_material(999, usuario_id=1, tipo_perfil="professor")
        assert exc.value.status_code == 404


class TestObterCaminhoArquivo:
    def test_retorna_caminho(self, service):
        mat = make_material(nome_arquivo="abc123.pdf", nome_original="apostila.pdf")
        service.repo.obter_com_relacionamentos.return_value = mat
        with patch("backend.services.material_service._get_upload_dir") as mock_dir:
            tmp = Path(tempfile.mkdtemp())
            (tmp / "abc123.pdf").write_bytes(b"fake")
            mock_dir.return_value = tmp
            path, nome = service.obter_caminho_arquivo(1)
            assert nome == "apostila.pdf"
            assert path.exists()

    def test_404_quando_material_nao_existe(self, service):
        service.repo.obter_com_relacionamentos.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.obter_caminho_arquivo(999)
        assert exc.value.status_code == 404


class TestNotificarAlunos:
    @pytest.mark.asyncio
    async def test_upload_notifica_alunos(self, service):
        mat = make_material()
        service.repo.create.return_value = mat
        file = UploadFile(filename="test.pdf", file=MagicMock())
        file.read = AsyncMock(return_value=b"%PDF-1.4 fake content")

        disciplina_mock = MagicMock()
        disciplina_mock.id = 1
        disciplina_mock.descricao = "Matemática"
        service.db.query.return_value.filter.return_value.first.return_value = disciplina_mock

        professor_mock = MagicMock()
        professor_mock.nome = "João Silva"
        service.usuario_repo.get_by_id.return_value = professor_mock

        diario_mock = MagicMock()
        diario_mock.aluno_id = 10
        service.diario_aluno_repo.listar_por_disciplina.return_value = [diario_mock]

        aluno_mock = MagicMock()
        aluno_mock.suap_id = "12345"
        service.aluno_repo.get_by_id.return_value = aluno_mock

        usuario_mock = MagicMock()
        usuario_mock.id = 100
        service.usuario_repo.get_by_suap_id.return_value = usuario_mock

        with patch("backend.services.material_service._get_upload_dir") as mock_dir:
            tmp = Path(tempfile.mkdtemp())
            mock_dir.return_value = tmp
            with patch("backend.services.material_service.NotificacaoService") as mock_notif_class:
                mock_notif = MagicMock()
                mock_notif_class.return_value = mock_notif
                await service.upload_material(
                    disciplina_id=1, usuario_id=1, file=file, descricao="Teste"
                )
                mock_notif.criar_notificacao.assert_called_once()
                call_kwargs = mock_notif.criar_notificacao.call_args[1]
                assert call_kwargs["tipo"] == "material_adicionado"
                assert call_kwargs["destino_tipo"] == "usuario"
                assert call_kwargs["destino_id"] == 100
                assert "João Silva" in call_kwargs["mensagem"]
                assert "Matemática" in call_kwargs["mensagem"]

    @pytest.mark.asyncio
    async def test_upload_sem_alunos_nao_falha(self, service):
        mat = make_material()
        service.repo.create.return_value = mat
        file = UploadFile(filename="test.pdf", file=MagicMock())
        file.read = AsyncMock(return_value=b"%PDF-1.4 fake content")

        disciplina_mock = MagicMock()
        disciplina_mock.id = 1
        disciplina_mock.descricao = "Matemática"
        service.db.query.return_value.filter.return_value.first.return_value = disciplina_mock

        professor_mock = MagicMock()
        professor_mock.nome = "João Silva"
        service.usuario_repo.get_by_id.return_value = professor_mock

        service.diario_aluno_repo.listar_por_disciplina.return_value = []

        with patch("backend.services.material_service._get_upload_dir") as mock_dir:
            tmp = Path(tempfile.mkdtemp())
            mock_dir.return_value = tmp
            with patch("backend.services.material_service.NotificacaoService") as mock_notif_class:
                mock_notif = MagicMock()
                mock_notif_class.return_value = mock_notif
                result = await service.upload_material(
                    disciplina_id=1, usuario_id=1, file=file, descricao="Teste"
                )
                assert result is not None
                mock_notif.criar_notificacao.assert_not_called()

    @pytest.mark.asyncio
    async def test_upload_aluno_sem_conta_nao_notifica(self, service):
        mat = make_material()
        service.repo.create.return_value = mat
        file = UploadFile(filename="test.pdf", file=MagicMock())
        file.read = AsyncMock(return_value=b"%PDF-1.4 fake content")

        disciplina_mock = MagicMock()
        disciplina_mock.id = 1
        disciplina_mock.descricao = "Matemática"
        service.db.query.return_value.filter.return_value.first.return_value = disciplina_mock

        professor_mock = MagicMock()
        professor_mock.nome = "João Silva"
        service.usuario_repo.get_by_id.return_value = professor_mock

        diario_mock = MagicMock()
        diario_mock.aluno_id = 10
        service.diario_aluno_repo.listar_por_disciplina.return_value = [diario_mock]

        aluno_mock = MagicMock()
        aluno_mock.suap_id = "12345"
        service.aluno_repo.get_by_id.return_value = aluno_mock

        service.usuario_repo.get_by_suap_id.return_value = None

        with patch("backend.services.material_service._get_upload_dir") as mock_dir:
            tmp = Path(tempfile.mkdtemp())
            mock_dir.return_value = tmp
            with patch("backend.services.material_service.NotificacaoService") as mock_notif_class:
                mock_notif = MagicMock()
                mock_notif_class.return_value = mock_notif
                result = await service.upload_material(
                    disciplina_id=1, usuario_id=1, file=file, descricao="Teste"
                )
                assert result is not None
                mock_notif.criar_notificacao.assert_not_called()

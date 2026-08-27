from __future__ import annotations
import logging
import os
import uuid
from pathlib import Path
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session
import magic
from backend.config import settings
from backend.models.disciplina import Disciplina
from backend.models.material import Material
from backend.repositories.aluno import AlunoRepository
from backend.repositories.diario_aluno import DiarioAlunoRepository
from backend.repositories.material import MaterialRepository
from backend.repositories.usuario import UsuarioRepository
from backend.schemas.material import MaterialResponse
from backend.services.notificacao_service import NotificacaoService

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS: set[str] = set()

MAGIC_BYTES = {
    "pdf": [b"%PDF"],
    "doc": [b"\xd0\xcf\x11\xe0"],
    "docx": [b"PK\x03\x04"],
    "ppt": [b"\xd0\xcf\x11\xe0"],
    "pptx": [b"PK\x03\x04"],
    "png": [b"\x89PNG"],
    "jpg": [b"\xff\xd8\xff"],
    "jpeg": [b"\xff\xd8\xff"],
    "txt": None,
}

def _get_allowed_extensions() -> set[str]:
    if not ALLOWED_EXTENSIONS:
        ALLOWED_EXTENSIONS.update(ext.strip().lower() for ext in settings.allowed_extensions.split(",") if ext.strip())
    return ALLOWED_EXTENSIONS


def _get_extension(filename: str) -> str:
    return Path(filename).suffix.lower().lstrip(".")


def _validate_file(filename: str, content_type: str, size: int, content: bytes) -> None:
    ext = _get_extension(filename)
    if ext not in _get_allowed_extensions():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de arquivo '.{ext}' nao permitido. Tipos aceitos: {settings.allowed_extensions}",
        )
    if size > settings.max_upload_size:
        max_mb = settings.max_upload_size // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Arquivo muito grande. Tamanho maximo: {max_mb}MB",
        )
    expected_magic = MAGIC_BYTES.get(ext)
    if expected_magic:
        if not any(content.startswith(m) for m in expected_magic):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Arquivo corrompido ou tipo invalido para extensao .{ext}",
            )
    
    # Validação de MIME type é apenas informativa, não bloqueante
    # Browsers podem enviar MIME types diferentes do detectado por magic
    if content_type:
        detected_mime = magic.from_buffer(content, mime=True)
        if detected_mime != content_type:
            logger.warning(
                "MIME type mismatch: esperado=%s, detectado=%s para arquivo %s",
                content_type, detected_mime, filename
            )


def _get_upload_dir() -> Path:
    base = Path(settings.uploads_dir)
    materiais_dir = base / "materiais"
    materiais_dir.mkdir(parents=True, exist_ok=True)
    return materiais_dir


class MaterialService:
    def __init__(self, db: Session):
        self.repo = MaterialRepository(db)
        self.db = db
        self.diario_aluno_repo = DiarioAlunoRepository(db)
        self.aluno_repo = AlunoRepository(db)
        self.usuario_repo = UsuarioRepository(db)

    def listar_materiais(self, disciplina_id: int, categoria: str | None = None) -> list[MaterialResponse]:
        materiais = self.repo.listar_por_disciplina(disciplina_id, categoria=categoria)
        result = []
        for m in materiais:
            resp = MaterialResponse.model_validate(m)
            if m.usuario:
                resp.usuario_nome = m.usuario.nome
            result.append(resp)
        return result

    def _get_categorias(self) -> set[str]:
        return {c.strip().lower() for c in settings.material_categorias.split(",") if c.strip()}

    async def upload_material(
        self,
        disciplina_id: int,
        usuario_id: int,
        file: UploadFile,
        descricao: str | None = None,
        categoria: str | None = None,
    ) -> MaterialResponse:
        content = await file.read()
        size = len(content)
        _validate_file(file.filename or "", file.content_type or "", size, content)

        cat = (categoria or "outro").strip().lower()
        if cat not in self._get_categorias():
            cat = "outro"

        ext = _get_extension(file.filename or "")
        nome_arquivo = f"{uuid.uuid4().hex}.{ext}"

        upload_dir = _get_upload_dir()
        file_path = upload_dir / nome_arquivo
        with open(file_path, "wb") as f:
            f.write(content)

        try:
            material = self.repo.create({
                "disciplina_id": disciplina_id,
                "usuario_id": usuario_id,
                "nome_original": file.filename or "arquivo",
                "nome_arquivo": nome_arquivo,
                "tipo_arquivo": file.content_type or "application/octet-stream",
                "tamanho": size,
                "descricao": descricao,
                "categoria": cat,
            })
            logger.info(
                "Material enviado: id=%s, disciplina_id=%s, arquivo=%s",
                material.id, disciplina_id, nome_arquivo,
            )
            try:
                self._notificar_alunos(material, disciplina_id, usuario_id)
            except Exception as e:
                logger.warning("Falha ao notificar alunos sobre material %s: %s", material.id, e)
            resp = MaterialResponse.model_validate(material)
            return resp
        except Exception:
            if file_path.exists():
                file_path.unlink()
            raise

    def obter_caminho_arquivo(self, material_id: int) -> tuple[Path, str]:
        material = self.repo.obter_com_relacionamentos(material_id)
        if not material:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Material nao encontrado",
            )
        file_path = _get_upload_dir() / material.nome_arquivo
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Arquivo nao encontrado no servidor",
            )
        return file_path, material.nome_original

    def deletar_material(
        self,
        material_id: int,
        usuario_id: int,
        tipo_perfil: str,
    ) -> bool:
        material = self.repo.get_by_id(material_id)
        if not material:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Material nao encontrado",
            )
        if material.usuario_id != usuario_id and tipo_perfil not in ("admin",):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Voce nao tem permissao para excluir este material",
            )
        file_path = _get_upload_dir() / material.nome_arquivo
        if file_path.exists():
            file_path.unlink()
        self.repo.delete(material_id)
        logger.info("Material deletado: id=%s", material_id)
        return True

    def _notificar_alunos(self, material: Material, disciplina_id: int, professor_usuario_id: int):
        disciplina = self.db.query(Disciplina).filter(Disciplina.id == disciplina_id).first()
        if not disciplina:
            return
        professor = self.usuario_repo.get_by_id(professor_usuario_id)
        professor_nome = professor.nome if professor else "Professor"
        diarios = self.diario_aluno_repo.listar_por_disciplina(disciplina_id)
        notif_service = NotificacaoService(self.db)
        for diario in diarios:
            aluno = self.aluno_repo.get_by_id(diario.aluno_id)
            if not aluno or not aluno.suap_id:
                continue
            usuario = self.usuario_repo.get_by_suap_id(aluno.suap_id)
            if not usuario:
                continue
            notif_service.criar_notificacao(
                tipo="material_adicionado",
                titulo="Novo material de estudo",
                mensagem=f"{professor_nome} adicionou o material '{material.nome_original}' na disciplina {disciplina.descricao}",
                remetente_id=professor_usuario_id,
                destino_tipo="usuario",
                destino_id=usuario.id,
            )

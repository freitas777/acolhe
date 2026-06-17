from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from backend.models.pendencia_validacao import PendenciaValidacao, StatusPendencia
from backend.models.aluno import Aluno
from backend.models.usuario import Usuario, TipoPerfil
from backend.services.auth_service import AuthService
from backend.security import (
    hash_senha,
    verificar_senha,
    criar_jwt,
    validar_jwt,
    is_jwt_local,
)


# ---------------------------------------------------------------------------
# Security: hash_senha / verificar_senha
# ---------------------------------------------------------------------------

class TestHashSenha:
    def test_retorna_formato_salt_dolar_hash(self):
        result = hash_senha("minhasenha")
        assert "$" in result
        parts = result.split("$", 1)
        assert len(parts) == 2
        assert len(parts[0]) == 32

    def test_senhas_iguais_geram_hashes_diferentes(self):
        h1 = hash_senha("minhasenha")
        h2 = hash_senha("minhasenha")
        assert h1 != h2


class TestVerificarSenha:
    def test_senha_correta_novo_formato(self):
        hashed = hash_senha("minhasenha")
        assert verificar_senha("minhasenha", hashed) is True

    def test_senha_incorreta_novo_formato(self):
        hashed = hash_senha("minhasenha")
        assert verificar_senha("errada", hashed) is False

    def test_senha_correta_formato_legado(self):
        import hashlib
        with patch("backend.security.settings") as mock_settings, \
             patch("backend.security._get_legacy_keys", return_value=["chave_legada"]):
            mock_settings.secret_key = "new-rotated-key"
            legacy_hash = hashlib.pbkdf2_hmac(
                "sha256", "minhasenha".encode(), "chave_legada".encode(), 100000
            ).hex()
            assert verificar_senha("minhasenha", legacy_hash) is True

    def test_senha_incorreta_formato_legado(self):
        with patch("backend.security.settings") as mock_settings, \
             patch("backend.security._get_legacy_keys", return_value=["chave_legada"]):
            mock_settings.secret_key = "new-rotated-key"
            assert verificar_senha("errada", "hash_qualquer_sem_cifrao") is False

    def test_legacy_key_nao_encontrada_retorna_false(self):
        import hashlib
        with patch("backend.security.settings") as mock_settings, \
             patch("backend.security._get_legacy_keys", return_value=["other_key"]):
            mock_settings.secret_key = "new-rotated-key"
            legacy_hash = hashlib.pbkdf2_hmac(
                "sha256", "minhasenha".encode(), "old_key".encode(), 100000
            ).hex()
            assert verificar_senha("minhasenha", legacy_hash) is False


# ---------------------------------------------------------------------------
# Security: JWT
# ---------------------------------------------------------------------------

class TestCriarJWT:
    def test_cria_token_valido(self):
        token = criar_jwt({"usuario_id": 1, "tipo_perfil": "professor"})
        assert isinstance(token, str)
        assert token.count(".") == 2

    def test_payload_contem_iat_e_exp(self):
        token = criar_jwt({"usuario_id": 1}, expira_em_horas=1)
        payload = validar_jwt(token)
        assert payload is not None
        assert "iat" in payload
        assert "exp" in payload
        assert payload["usuario_id"] == 1

    def test_expiracao_customizada(self):
        token = criar_jwt({"usuario_id": 1}, expira_em_horas=48)
        payload = validar_jwt(token)
        assert payload is not None
        assert payload["exp"] - payload["iat"] == 48 * 3600


class TestValidarJWT:
    def test_token_valido(self):
        token = criar_jwt({"usuario_id": 1, "tipo_perfil": "admin"})
        payload = validar_jwt(token)
        assert payload is not None
        assert payload["usuario_id"] == 1
        assert payload["tipo_perfil"] == "admin"

    def test_token_invalido_retorna_none(self):
        assert validar_jwt("invalido") is None

    def test_token_com_partes_incorretas(self):
        assert validar_jwt("a.b") is None
        assert validar_jwt("a.b.c.d") is None

    @patch("backend.security.time")
    def test_token_expirado_retorna_none(self, mock_time):
        mock_time.time.return_value = 9999999999
        token = criar_jwt({"usuario_id": 1}, expira_em_horas=1)
        mock_time.time.return_value = 9999999999 + 7200
        assert validar_jwt(token) is None

    def test_header_sem_typ_acolhe_local(self):
        import base64
        import json
        import hmac
        import hashlib
        from backend.config import settings

        header = base64.urlsafe_b64encode(
            json.dumps({"alg": "HS256", "typ": "other"}).encode()
        ).rstrip(b"=")
        payload_b64 = base64.urlsafe_b64encode(
            json.dumps({"sub": "1", "exp": 9999999999}).encode()
        ).rstrip(b"=")
        signing_input = header + b"." + payload_b64
        sig = hmac.new(settings.secret_key.encode(), signing_input, hashlib.sha256).digest()
        sig_b64 = base64.urlsafe_b64encode(sig).rstrip(b"=")
        token = (signing_input + b"." + sig_b64).decode()
        assert validar_jwt(token) is None


class TestIsJWTLocal:
    def test_token_local_retorna_true(self):
        token = criar_jwt({"usuario_id": 1})
        assert is_jwt_local(token) is True

    def test_token_muito_longo_retorna_false(self):
        assert is_jwt_local("a" * 501) is False

    def test_sem_dois_pontos_retorna_false(self):
        assert is_jwt_local("abc") is False

    def test_header_nao_acolhe_local(self):
        import base64
        import json
        header = base64.urlsafe_b64encode(
            json.dumps({"alg": "HS256", "typ": "other"}).encode()
        ).rstrip(b"=")
        token = header.decode() + ".payload.sig"
        assert is_jwt_local(token) is False


# ---------------------------------------------------------------------------
# AuthService sync method tests (with mocked repos)
# ---------------------------------------------------------------------------

def make_usuario(
    id: int = 1,
    suap_id: str = "00001",
    nome: str = "Maria",
    email: str = "maria@escola.edu.br",
    tipo_perfil: str = "professor",
    aprovado_napne: bool = False,
) -> Usuario:
    u = Usuario()
    u.id = id
    u.suap_id = suap_id
    u.nome = nome
    u.email = email
    u.tipo_perfil = tipo_perfil
    u.aprovado_napne = aprovado_napne
    return u


def make_aluno(id: int = 1, nome: str = "João", status_acompanhamento: str = "aguardando_indicacao") -> Aluno:
    a = Aluno()
    a.id = id
    a.nome = nome
    a.status_acompanhamento = status_acompanhamento
    return a


def make_pendencia(id: int = 1, aluno_id: int = 1, status: StatusPendencia = StatusPendencia.pendente) -> PendenciaValidacao:
    p = PendenciaValidacao()
    p.id = id
    p.aluno_id = aluno_id
    p.status = status
    p.indicado_por_id = 10
    p.validado_por_id = None
    p.validado_em = None
    p.motivo = None
    return p


@pytest.fixture
def auth_service():
    svc = AuthService.__new__(AuthService)
    svc.db = MagicMock()
    svc.usuario_repo = MagicMock()
    svc.disciplina_repo = MagicMock()
    svc.diario_aluno_repo = MagicMock()
    svc.aluno_repo = MagicMock()
    svc.pendencia_repo = MagicMock()
    svc.suap_service = MagicMock()
    return svc


# ---------------------------------------------------------------------------
# obter_usuario_atual
# ---------------------------------------------------------------------------

class TestObterUsuarioAtual:
    def test_retorna_usuario_existente(self, auth_service):
        auth_service.usuario_repo.get_by_id.return_value = make_usuario()
        result = auth_service.obter_usuario_atual(1)
        assert result.id == 1

    def test_levanta_404_quando_nao_encontrado(self, auth_service):
        auth_service.usuario_repo.get_by_id.return_value = None
        with pytest.raises(HTTPException) as exc:
            auth_service.obter_usuario_atual(99)
        assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# obter_disciplinas
# ---------------------------------------------------------------------------

class TestObterDisciplinas:
    def test_delega_para_repositorio(self, auth_service):
        auth_service.disciplina_repo.listar_por_usuario.return_value = []
        result = auth_service.obter_disciplinas(1, "2026.1")
        auth_service.disciplina_repo.listar_por_usuario.assert_called_once_with(1, "2026.1")
        assert result == []


# ---------------------------------------------------------------------------
# obter_alunos_assistidos
# ---------------------------------------------------------------------------

class TestObterAlunosAssistidos:
    def test_delega_para_repositorio(self, auth_service):
        auth_service.diario_aluno_repo.listar_por_disciplina.return_value = []
        result = auth_service.obter_alunos_assistidos(5)
        auth_service.diario_aluno_repo.listar_por_disciplina.assert_called_once_with(5)


# ---------------------------------------------------------------------------
# obter_pendencias
# ---------------------------------------------------------------------------

class TestObterPendencias:
    def test_retorna_pendencias_pendentes(self, auth_service):
        auth_service.pendencia_repo.listar_pendentes.return_value = [make_pendencia()]
        result = auth_service.obter_pendencias()
        assert len(result) == 1


# ---------------------------------------------------------------------------
# validar_pendencia
# ---------------------------------------------------------------------------

class TestValidarPendencia:
    def test_valida_pendencia_com_sucesso(self, auth_service):
        pendencia = make_pendencia()
        pendencia.aluno_id = 1
        auth_service.pendencia_repo.get_by_id.return_value = pendencia
        auth_service.pendencia_repo.update.return_value = pendencia
        aluno = make_aluno()
        auth_service.aluno_repo.get_by_id.return_value = aluno

        result = auth_service.validar_pendencia(1, validado_por_id=10, acao=StatusPendencia.validado.value)

        assert result is pendencia
        auth_service.pendencia_repo.update.assert_called_once()
        auth_service.db.commit.assert_called_once()

    def test_levanta_404_pendencia_nao_encontrada(self, auth_service):
        auth_service.pendencia_repo.get_by_id.return_value = None
        with pytest.raises(HTTPException) as exc:
            auth_service.validar_pendencia(99, validado_por_id=10, acao="validado")
        assert exc.value.status_code == 404

    def test_levanta_400_pendencia_ja_processada(self, auth_service):
        pendencia = make_pendencia(status=StatusPendencia.validado)
        auth_service.pendencia_repo.get_by_id.return_value = pendencia
        with pytest.raises(HTTPException) as exc:
            auth_service.validar_pendencia(1, validado_por_id=10, acao="validado")
        assert exc.value.status_code == 400

    def test_rejeicao_altera_status_para_rejeitado(self, auth_service):
        pendencia = make_pendencia()
        pendencia.aluno_id = 1
        auth_service.pendencia_repo.get_by_id.return_value = pendencia
        auth_service.pendencia_repo.update.return_value = pendencia
        aluno = make_aluno()
        auth_service.aluno_repo.get_by_id.return_value = aluno

        auth_service.validar_pendencia(1, validado_por_id=10, acao=StatusPendencia.rejeitado.value)

        assert aluno.status_acompanhamento == "rejeitado"
        auth_service.db.commit.assert_called_once()

    def test_validacao_altera_status_para_ativo(self, auth_service):
        pendencia = make_pendencia()
        pendencia.aluno_id = 1
        auth_service.pendencia_repo.get_by_id.return_value = pendencia
        auth_service.pendencia_repo.update.return_value = pendencia
        aluno = make_aluno(status_acompanhamento="aguardando_indicacao")
        auth_service.aluno_repo.get_by_id.return_value = aluno

        auth_service.validar_pendencia(1, validado_por_id=10, acao=StatusPendencia.validado.value)

        assert aluno.status_acompanhamento == "ativo"


# ---------------------------------------------------------------------------
# criar_pendencia
# ---------------------------------------------------------------------------

class TestCriarPendencia:
    def test_cria_pendencia_com_sucesso(self, auth_service):
        auth_service.aluno_repo.get_by_id.return_value = make_aluno()
        auth_service.pendencia_repo.get_pendente_por_aluno.return_value = None
        auth_service.pendencia_repo.create.return_value = make_pendencia()

        result = auth_service.criar_pendencia(aluno_id=1, indicado_por_id=10)

        auth_service.pendencia_repo.create.assert_called_once()
        payload = auth_service.pendencia_repo.create.call_args[0][0]
        assert payload["status"] == StatusPendencia.pendente

    def test_levanta_404_aluno_nao_encontrado(self, auth_service):
        auth_service.aluno_repo.get_by_id.return_value = None
        with pytest.raises(HTTPException) as exc:
            auth_service.criar_pendencia(aluno_id=99, indicado_por_id=10)
        assert exc.value.status_code == 404

    def test_levanta_400_pendencia_ja_existe(self, auth_service):
        auth_service.aluno_repo.get_by_id.return_value = make_aluno()
        auth_service.pendencia_repo.get_pendente_por_aluno.return_value = make_pendencia()
        with pytest.raises(HTTPException) as exc:
            auth_service.criar_pendencia(aluno_id=1, indicado_por_id=10)
        assert exc.value.status_code == 400


# ---------------------------------------------------------------------------
# atualizar_perfil_usuario
# ---------------------------------------------------------------------------

class TestAtualizarPerfilUsuario:
    def test_atualiza_para_psicopedagogo(self, auth_service):
        usuario = make_usuario(tipo_perfil="servidor")
        auth_service.usuario_repo.get_by_id.return_value = usuario
        auth_service.usuario_repo.get_by_id.return_value = usuario

        result = auth_service.atualizar_perfil_usuario(1, "psicopedagogo")

        assert usuario.tipo_perfil == "psicopedagogo"
        assert usuario.aprovado_napne is True
        auth_service.db.commit.assert_called_once()

    def test_atualiza_para_servidor(self, auth_service):
        usuario = make_usuario(tipo_perfil="psicopedagogo", aprovado_napne=True)
        auth_service.usuario_repo.get_by_id.return_value = usuario

        result = auth_service.atualizar_perfil_usuario(1, "servidor")

        assert usuario.tipo_perfil == "servidor"
        assert usuario.aprovado_napne is False

    def test_levanta_404_usuario_nao_encontrado(self, auth_service):
        auth_service.usuario_repo.get_by_id.return_value = None
        with pytest.raises(HTTPException) as exc:
            auth_service.atualizar_perfil_usuario(99, "servidor")
        assert exc.value.status_code == 404

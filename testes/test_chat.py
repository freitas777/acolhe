from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from backend.models.conversa import Conversa
from backend.models.mensagem import Mensagem
from backend.models.aluno import Aluno
from backend.models.perfil_aluno import PerfilAluno
from backend.schemas.chat import ChatRequisicao, ConversaCriar, MensagemResposta
from backend.services.chat_service import ChatService, _para_conversa_resposta, _para_mensagem_resposta


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_conversa(
    id: str = "conv-1",
    titulo: str = "Nova conversa",
    usuario_id: int = 1,
    aluno_id: int | None = None,
) -> Conversa:
    c = Conversa()
    c.id = id
    c.titulo = titulo
    c.usuario_id = usuario_id
    c.aluno_id = aluno_id
    c.criada_em = datetime(2024, 1, 1, tzinfo=timezone.utc)
    c.mensagens = []
    c.aluno = None
    if aluno_id:
        c.aluno = make_aluno(id=aluno_id)
    return c


def make_mensagem(
    id: str = "msg-1",
    conversa_id: str = "conv-1",
    papel: str = "usuario",
    conteudo: str = "Olá",
) -> Mensagem:
    m = Mensagem()
    m.id = id
    m.conversa_id = conversa_id
    m.papel = papel
    m.conteudo = conteudo
    m.criada_em = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return m


def make_aluno(id: int = 1, nome: str = "João") -> Aluno:
    a = Aluno()
    a.id = id
    a.nome = nome
    return a


def make_perfil(aluno_id: int = 1) -> PerfilAluno:
    p = PerfilAluno()
    p.id = 1
    p.aluno_id = aluno_id
    p.nivel_atencao = None
    p.dificuldade_leitura = False
    p.preferencia = None
    p.interesses = None
    p.diagnostico = None
    return p


@pytest.fixture
def service():
    svc = ChatService.__new__(ChatService)
    svc.conversa_repo = MagicMock()
    svc.mensagem_repo = MagicMock()
    svc.aluno_repo = MagicMock()
    svc.db = MagicMock()
    return svc


# ---------------------------------------------------------------------------
# _para_mensagem_resposta
# ---------------------------------------------------------------------------

class TestParaMensagemResposta:
    def test_mapeia_papel_usuario(self):
        msg = make_mensagem(papel="usuario")
        resp = _para_mensagem_resposta(msg)
        assert resp.role == "user"

    def test_mapeia_papel_assistente(self):
        msg = make_mensagem(papel="assistente")
        resp = _para_mensagem_resposta(msg)
        assert resp.role == "assistant"


# ---------------------------------------------------------------------------
# _para_conversa_resposta
# ---------------------------------------------------------------------------

class TestParaConversaResposta:
    def test_sem_aluno(self):
        conv = make_conversa(aluno_id=None)
        resp = _para_conversa_resposta(conv)
        assert resp.aluno_id is None
        assert resp.aluno_nome is None

    def test_com_aluno(self):
        conv = make_conversa(aluno_id=1)
        resp = _para_conversa_resposta(conv)
        assert resp.aluno_id == 1
        assert resp.aluno_nome == "João"


# ---------------------------------------------------------------------------
# listar_conversas
# ---------------------------------------------------------------------------

class TestListarConversas:
    def test_psicopedagogo_ve_todas(self, service):
        service.conversa_repo.listar_com_mensagens.return_value = [make_conversa()]
        result = service.listar_conversas(usuario_id=1, tipo_perfil="psicopedagogo")
        service.conversa_repo.listar_com_mensagens.assert_called_once_with()
        assert len(result) == 1

    def test_aluno_ve_apenas_as_suas(self, service):
        service.conversa_repo.listar_com_mensagens.return_value = [make_conversa()]
        result = service.listar_conversas(usuario_id=1, tipo_perfil="aluno")
        service.conversa_repo.listar_com_mensagens.assert_called_once_with(usuario_id=1)

    def test_admin_ve_todas(self, service):
        service.conversa_repo.listar_com_mensagens.return_value = []
        result = service.listar_conversas(usuario_id=1, tipo_perfil="admin")
        service.conversa_repo.listar_com_mensagens.assert_called_once_with()


# ---------------------------------------------------------------------------
# obter_conversa
# ---------------------------------------------------------------------------

class TestObterConversa:
    def test_retorna_conversa_existente(self, service):
        conv = make_conversa(usuario_id=1)
        service.conversa_repo.obter_com_mensagens.return_value = conv
        result = service.obter_conversa("conv-1", usuario_id=1, tipo_perfil="aluno")
        assert result.id == "conv-1"

    def test_levanta_404_nao_encontrada(self, service):
        service.conversa_repo.obter_com_mensagens.return_value = None
        with pytest.raises(HTTPException) as exc:
            service.obter_conversa("conv-x", usuario_id=1)
        assert exc.value.status_code == 404

    def test_levanta_403_usuario_nao_dono(self, service):
        conv = make_conversa(usuario_id=2)
        service.conversa_repo.obter_com_mensagens.return_value = conv
        with pytest.raises(HTTPException) as exc:
            service.obter_conversa("conv-1", usuario_id=1, tipo_perfil="aluno")
        assert exc.value.status_code == 403

    def test_psicopedagogo_acessa_qualquer_conversa(self, service):
        conv = make_conversa(usuario_id=2)
        service.conversa_repo.obter_com_mensagens.return_value = conv
        result = service.obter_conversa("conv-1", usuario_id=1, tipo_perfil="psicopedagogo")
        assert result.id == "conv-1"


# ---------------------------------------------------------------------------
# _verificar_propriedade
# ---------------------------------------------------------------------------

class TestVerificarPropriedade:
    def test_dono_tem_acesso(self, service):
        conv = make_conversa(usuario_id=1)
        service._verificar_propriedade(conv, usuario_id=1, tipo_perfil="aluno")

    def test_nao_dono_sem_permissao(self, service):
        conv = make_conversa(usuario_id=2)
        with pytest.raises(HTTPException) as exc:
            service._verificar_propriedade(conv, usuario_id=1, tipo_perfil="aluno")
        assert exc.value.status_code == 403

    def test_nao_dono_psicopedagogo_tem_acesso(self, service):
        conv = make_conversa(usuario_id=2)
        service._verificar_propriedade(conv, usuario_id=1, tipo_perfil="psicopedagogo")

    def test_nao_dono_admin_tem_acesso(self, service):
        conv = make_conversa(usuario_id=2)
        service._verificar_propriedade(conv, usuario_id=1, tipo_perfil="admin")


# ---------------------------------------------------------------------------
# criar_conversa
# ---------------------------------------------------------------------------

class TestCriarConversa:
    @pytest.mark.asyncio
    async def test_cria_conversa_sem_aluno(self, service):
        conv = make_conversa(aluno_id=None)
        service.conversa_repo.create.return_value = conv

        with patch("backend.services.chat_service.ai_service") as mock_ai:
            mock_ai.iniciar_sessao = AsyncMock()
            result = await service.criar_conversa(ConversaCriar(titulo="Teste"), usuario_id=1)

        assert result.id == "conv-1"

    @pytest.mark.asyncio
    async def test_cria_conversa_com_aluno_com_perfil(self, service):
        conv = make_conversa(aluno_id=1)
        service.conversa_repo.create.return_value = conv
        aluno = make_aluno()
        aluno.perfil = make_perfil()
        service.aluno_repo.get_with_profile.return_value = aluno

        with patch("backend.services.chat_service.ai_service") as mock_ai:
            mock_ai.iniciar_sessao = AsyncMock()
            mock_ai.construir_contexto_aluno.return_value = "contexto do aluno"
            result = await service.criar_conversa(
                ConversaCriar(titulo="Teste", aluno_id=1), usuario_id=1
            )

        assert result.aluno_id == 1
        mock_ai.iniciar_sessao.assert_called_once()

    @pytest.mark.asyncio
    async def test_cria_conversa_com_aluno_sem_perfil(self, service):
        conv = make_conversa(aluno_id=1)
        service.conversa_repo.create.return_value = conv
        aluno = make_aluno()
        aluno.perfil = None
        service.aluno_repo.get_with_profile.return_value = aluno

        with patch("backend.services.chat_service.ai_service") as mock_ai:
            mock_ai.iniciar_sessao = AsyncMock()
            result = await service.criar_conversa(
                ConversaCriar(titulo="Teste", aluno_id=1), usuario_id=1
            )

        mock_ai.iniciar_sessao.assert_called_once_with(conv.id, contexto_aluno=None)


# ---------------------------------------------------------------------------
# deletar_conversa
# ---------------------------------------------------------------------------

class TestDeletarConversa:
    @pytest.mark.asyncio
    async def test_deleta_com_sucesso(self, service):
        conv = make_conversa(usuario_id=1)
        service.conversa_repo.get_by_id.return_value = conv
        service.conversa_repo.delete.return_value = True

        with patch("backend.services.chat_service.ai_service") as mock_ai:
            mock_ai.encerrar_sessao = AsyncMock()
            result = await service.deletar_conversa("conv-1", usuario_id=1, tipo_perfil="aluno")

        assert result is True
        mock_ai.encerrar_sessao.assert_called_once_with("conv-1")

    @pytest.mark.asyncio
    async def test_levanta_404_nao_encontrada(self, service):
        service.conversa_repo.get_by_id.return_value = None
        with pytest.raises(HTTPException) as exc:
            await service.deletar_conversa("conv-x", usuario_id=1)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_levanta_403_usuario_nao_dono(self, service):
        conv = make_conversa(usuario_id=2)
        service.conversa_repo.get_by_id.return_value = conv
        with pytest.raises(HTTPException) as exc:
            await service.deletar_conversa("conv-1", usuario_id=1, tipo_perfil="aluno")
        assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# enviar_mensagem
# ---------------------------------------------------------------------------

class TestEnviarMensagem:
    @pytest.mark.asyncio
    async def test_cria_nova_conversa_quando_sem_conversation_id(self, service):
        conv = make_conversa()
        service.conversa_repo.obter_com_mensagens.return_value = conv
        service.conversa_repo.create.return_value = conv
        msg_user = make_mensagem(papel="usuario", conteudo="Olá")
        msg_ai = make_mensagem(id="msg-2", papel="assistente", conteudo="Oi!")
        service.mensagem_repo.create.side_effect = [msg_user, msg_ai]

        with patch("backend.services.chat_service.ai_service") as mock_ai:
            mock_ai.iniciar_sessao = AsyncMock()
            mock_ai.gerar_resposta = AsyncMock(return_value="Oi!")
            result = await service.enviar_mensagem(
                ChatRequisicao(message="Olá"), usuario_id=1, tipo_perfil="aluno"
            )

        assert result.conversation_id == "conv-1"

    @pytest.mark.asyncio
    async def test_envia_em_conversa_existente(self, service):
        conv = make_conversa(usuario_id=1)
        conv.mensagens = [make_mensagem()]
        service.conversa_repo.obter_com_mensagens.return_value = conv
        msg_user = make_mensagem(papel="usuario", conteudo="Olá")
        msg_ai = make_mensagem(id="msg-2", papel="assistente", conteudo="Oi!")
        service.mensagem_repo.create.side_effect = [msg_user, msg_ai]

        with patch("backend.services.chat_service.ai_service") as mock_ai:
            mock_ai.gerar_resposta = AsyncMock(return_value="Oi!")
            mock_ai.garantir_sessao_com_contexto = AsyncMock()
            result = await service.enviar_mensagem(
                ChatRequisicao(message="Olá", conversation_id="conv-1"),
                usuario_id=1,
                tipo_perfil="aluno",
            )

        assert result.conversation_id == "conv-1"

    @pytest.mark.asyncio
    async def test_erro_ia_retorna_mensagem_default(self, service):
        conv = make_conversa(usuario_id=1)
        conv.mensagens = [make_mensagem()]
        service.conversa_repo.obter_com_mensagens.return_value = conv
        msg_user = make_mensagem(papel="usuario", conteudo="Olá")
        msg_ai = make_mensagem(id="msg-2", papel="assistente", conteudo="Desculpe, estou com dificuldades para responder no momento. Tente novamente.")
        service.mensagem_repo.create.side_effect = [msg_user, msg_ai]

        with patch("backend.services.chat_service.ai_service") as mock_ai:
            mock_ai.gerar_resposta = AsyncMock(side_effect=RuntimeError("IA falhou"))
            mock_ai.garantir_sessao_com_contexto = AsyncMock()
            result = await service.enviar_mensagem(
                ChatRequisicao(message="Olá", conversation_id="conv-1"),
                usuario_id=1,
            )

        assert "dificuldades" in result.assistant_message.content

    @pytest.mark.asyncio
    async def test_levanta_404_conversa_nao_encontrada(self, service):
        service.conversa_repo.obter_com_mensagens.return_value = None
        with pytest.raises(HTTPException) as exc:
            await service.enviar_mensagem(
                ChatRequisicao(message="OlÃ¡", conversation_id="conv-x"),
                usuario_id=1,
            )
        assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# obter_ou_criar_conversa_disciplina
# ---------------------------------------------------------------------------

class TestObterOuCriarConversaDisciplina:
    @pytest.mark.asyncio
    async def test_cria_conversa_com_aluno_id_para_aluno(self, service):
        aluno = make_aluno(id=5)
        aluno.perfil = make_perfil(aluno_id=5)
        service.aluno_repo.get_by_suap_id.return_value = aluno
        service.disciplina_repo.get_by_id.return_value = MagicMock(
            descricao="MatemÃ¡tica", sigla="MAT", professor="Prof X",
            semestre="2026.1", codigo_turma="T01",
        )
        conv = make_conversa(id="conv-disc", usuario_id=1, aluno_id=5)
        conv.disciplina = MagicMock(descricao="MatemÃ¡tica", sigla="MAT")
        service.conversa_repo.obter_por_usuario_e_disciplina.return_value = None
        service.conversa_repo.create.return_value = conv

        with patch("backend.services.chat_service.ai_service") as mock_ai:
            mock_ai.iniciar_sessao = AsyncMock()
            mock_ai.construir_contexto_aluno.return_value = "contexto aluno"
            mock_ai.construir_contexto_disciplina.return_value = "contexto disciplina"
            result = await service.obter_ou_criar_conversa_disciplina(
                disciplina_id=10, usuario_id=1, tipo_perfil="aluno", suap_id="12345",
            )

        service.aluno_repo.get_by_suap_id.assert_called_once_with("12345")
        service.conversa_repo.create.assert_called_once()
        create_call_kwargs = service.conversa_repo.create.call_args[0][0]
        assert create_call_kwargs["aluno_id"] == 5
        mock_ai.iniciar_sessao.assert_called_once()
        call_kwargs = mock_ai.iniciar_sessao.call_args[1]
        assert call_kwargs["contexto_aluno"] == "contexto aluno"
        assert call_kwargs["contexto_disciplina"] == "contexto disciplina"

    @pytest.mark.asyncio
    async def test_cria_conversa_sem_aluno_id_para_professor(self, service):
        service.disciplina_repo.get_by_id.return_value = MagicMock(
            descricao="FÃ­sica", sigla="FIS", professor="Prof Y",
            semestre="2026.1", codigo_turma="T02",
        )
        conv = make_conversa(id="conv-disc2", usuario_id=2)
        conv.disciplina = MagicMock(descricao="FÃ­sica", sigla="FIS")
        service.conversa_repo.obter_por_usuario_e_disciplina.return_value = None
        service.conversa_repo.create.return_value = conv

        with patch("backend.services.chat_service.ai_service") as mock_ai:
            mock_ai.iniciar_sessao = AsyncMock()
            mock_ai.construir_contexto_disciplina.return_value = "contexto disciplina"
            result = await service.obter_ou_criar_conversa_disciplina(
                disciplina_id=20, usuario_id=2, tipo_perfil="professor", suap_id="99999",
            )

        service.aluno_repo.get_by_suap_id.assert_not_called()
        create_call_kwargs = service.conversa_repo.create.call_args[0][0]
        assert create_call_kwargs["aluno_id"] is None

    @pytest.mark.asyncio
    async def test_cria_conversa_sem_aluno_id_quando_aluno_nao_encontrado(self, service):
        service.aluno_repo.get_by_suap_id.return_value = None
        service.disciplina_repo.get_by_id.return_value = MagicMock(
            descricao="QuÃ­mica", sigla="QUI", professor="Prof Z",
            semestre="2026.1", codigo_turma="T03",
        )
        conv = make_conversa(id="conv-disc3", usuario_id=3)
        conv.disciplina = MagicMock(descricao="QuÃ­mica", sigla="QUI")
        service.conversa_repo.obter_por_usuario_e_disciplina.return_value = None
        service.conversa_repo.create.return_value = conv

        with patch("backend.services.chat_service.ai_service") as mock_ai:
            mock_ai.iniciar_sessao = AsyncMock()
            mock_ai.construir_contexto_disciplina.return_value = "contexto disciplina"
            result = await service.obter_ou_criar_conversa_disciplina(
                disciplina_id=30, usuario_id=3, tipo_perfil="aluno", suap_id="00000",
            )

        service.aluno_repo.get_by_suap_id.assert_called_once_with("00000")
        create_call_kwargs = service.conversa_repo.create.call_args[0][0]
        assert create_call_kwargs["aluno_id"] is None

    @pytest.mark.asyncio
    async def test_reutiliza_conversa_existente(self, service):
        conv = make_conversa(id="conv-exist", usuario_id=1, aluno_id=5)
        conv.disciplina = MagicMock(descricao="Biologia", sigla="BIO")
        conv.mensagens = [make_mensagem()]
        service.conversa_repo.obter_por_usuario_e_disciplina.return_value = conv
        service.mensagem_repo.listar_por_conversa.return_value = [make_mensagem()]

        with patch("backend.services.chat_service.ai_service") as mock_ai:
            mock_ai.garantir_sessao_com_contexto = AsyncMock()
            mock_ai.construir_contexto_disciplina.return_value = "contexto disciplina"
            result = await service.obter_ou_criar_conversa_disciplina(
                disciplina_id=40, usuario_id=1, tipo_perfil="aluno", suap_id="12345",
            )

        service.conversa_repo.create.assert_not_called()
        mock_ai.garantir_sessao_com_contexto.assert_called_once()

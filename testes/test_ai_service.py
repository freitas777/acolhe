from __future__ import annotations

import asyncio
from collections import OrderedDict
from unittest.mock import MagicMock, patch

import pytest

from backend.services.ai_service import AIService, INSTRUCAO_SISTEMA, MAX_SESSOES, MAX_MODELOS


# ---------------------------------------------------------------------------
# construir_contexto_aluno
# ---------------------------------------------------------------------------

class TestConstruirContextoAluno:
    def test_contexto_minimo(self):
        svc = AIService.__new__(AIService)
        aluno = MagicMock(nome="João", observacoes=None)
        perfil = MagicMock(nivel_atencao=None, dificuldade_leitura=False, preferencia=None, interesses=None, diagnostico=None)
        resultado = svc.construir_contexto_aluno(aluno, perfil)
        assert "João" in resultado
        assert "não informado" in resultado

    def test_contexto_completo(self):
        svc = AIService.__new__(AIService)
        nivel = MagicMock(value="alto")
        pref = MagicMock(value="visual")
        aluno = MagicMock(nome="Maria", observacoes="Tem TDAH")
        perfil = MagicMock(nivel_atencao=nivel, dificuldade_leitura=True, preferencia=pref, interesses="matemática", diagnostico="TDAH")
        resultado = svc.construir_contexto_aluno(aluno, perfil)
        assert "Maria" in resultado
        assert "alto" in resultado
        assert "Sim" in resultado
        assert "visual" in resultado
        assert "matemática" in resultado
        assert "TDAH" in resultado
        assert "Tem TDAH" in resultado

    def test_contexto_sem_observacoes_nao_inclui_linha(self):
        svc = AIService.__new__(AIService)
        aluno = MagicMock(nome="Ana", observacoes=None)
        perfil = MagicMock(nivel_atencao=None, dificuldade_leitura=False, preferencia=None, interesses=None, diagnostico=None)
        resultado = svc.construir_contexto_aluno(aluno, perfil)
        assert "Observações" not in resultado


# ---------------------------------------------------------------------------
# _obter_modelo_com_contexto (LRU cache)
# ---------------------------------------------------------------------------

class TestObterModeloComContexto:
    def test_cria_modelo_novo(self):
        svc = AIService.__new__(AIService)
        svc._modelos_por_contexto = OrderedDict()
        mock_model = MagicMock()
        with patch("backend.services.ai_service.genai") as mock_genai, \
             patch("backend.services.ai_service.settings") as mock_settings:
            mock_genai.GenerativeModel.return_value = mock_model
            mock_settings.gemini_model = "gemini-pro"
            result = svc._obter_modelo_com_contexto("contexto A")
        assert result is mock_model
        assert len(svc._modelos_por_contexto) == 1

    def test_reutiliza_modelo_cacheado(self):
        svc = AIService.__new__(AIService)
        svc._modelos_por_contexto = OrderedDict()
        mock_model = MagicMock()
        with patch("backend.services.ai_service.genai") as mock_genai, \
             patch("backend.services.ai_service.settings") as mock_settings:
            mock_genai.GenerativeModel.return_value = mock_model
            mock_settings.gemini_model = "gemini-pro"
            svc._obter_modelo_com_contexto("contexto A")
            svc._obter_modelo_com_contexto("contexto A")
        mock_genai.GenerativeModel.assert_called_once()

    def test_lru_evict_quando_excede_max(self):
        svc = AIService.__new__(AIService)
        svc._modelos_por_contexto = OrderedDict()
        mock_model = MagicMock()
        with patch("backend.services.ai_service.genai") as mock_genai, \
             patch("backend.services.ai_service.settings") as mock_settings:
            mock_genai.GenerativeModel.return_value = mock_model
            mock_settings.gemini_model = "gemini-pro"
            for i in range(MAX_MODELOS + 1):
                svc._obter_modelo_com_contexto(f"contexto {i}")
        assert len(svc._modelos_por_contexto) == MAX_MODELOS


# ---------------------------------------------------------------------------
# _criar_sessao / LRU sessões
# ---------------------------------------------------------------------------

class TestCriarSessao:
    def test_cria_sessao_sem_contexto(self):
        svc = AIService.__new__(AIService)
        svc._sessoes = OrderedDict()
        svc._sessao_contexto = {}
        svc._modelos_por_contexto = OrderedDict()
        mock_model = MagicMock()
        svc._model = mock_model
        mock_session = MagicMock()
        mock_model.start_chat.return_value = mock_session

        svc._criar_sessao("conv-1", contexto_aluno=None)

        assert "conv-1" in svc._sessoes
        assert "conv-1" not in svc._sessao_contexto
        mock_model.start_chat.assert_called_once()
        history = mock_model.start_chat.call_args[1]["history"]
        assert history[0]["role"] == "user"
        assert INSTRUCAO_SISTEMA in history[0]["parts"][0]

    def test_cria_sessao_com_contexto(self):
        svc = AIService.__new__(AIService)
        svc._sessoes = OrderedDict()
        svc._sessao_contexto = {}
        svc._modelos_por_contexto = OrderedDict()
        mock_model_ctx = MagicMock()
        svc._modelos_por_contexto["some_key"] = mock_model_ctx
        mock_session = MagicMock()
        mock_model_ctx.start_chat.return_value = mock_session

        with patch.object(svc, "_obter_modelo_com_contexto", return_value=mock_model_ctx):
            svc._criar_sessao("conv-1", contexto_aluno="contexto do aluno")

        assert "conv-1" in svc._sessoes
        assert svc._sessao_contexto["conv-1"] == "contexto do aluno"
        history = mock_model_ctx.start_chat.call_args[1]["history"]
        assert "contexto do aluno" in history[0]["parts"][0]

    def test_lru_evict_sessoes(self):
        svc = AIService.__new__(AIService)
        svc._sessoes = OrderedDict()
        svc._sessao_contexto = {}
        svc._modelos_por_contexto = OrderedDict()
        mock_model = MagicMock()
        svc._model = mock_model
        mock_model.start_chat.return_value = MagicMock()

        for i in range(MAX_SESSOES + 1):
            svc._criar_sessao(f"conv-{i}")

        assert len(svc._sessoes) == MAX_SESSOES


# ---------------------------------------------------------------------------
# encerrar_sessao
# ---------------------------------------------------------------------------

class TestEncerrarSessao:
    @pytest.mark.asyncio
    async def test_encerra_sessao_existente(self):
        svc = AIService.__new__(AIService)
        svc._lock = asyncio.Lock()
        svc._sessoes = OrderedDict()
        svc._sessao_contexto = {"conv-1": "ctx"}
        svc._modelos_por_contexto = OrderedDict()
        mock_model = MagicMock()
        svc._model = mock_model
        mock_model.start_chat.return_value = MagicMock()
        svc._criar_sessao("conv-1")

        await svc.encerrar_sessao("conv-1")

        assert "conv-1" not in svc._sessoes
        assert "conv-1" not in svc._sessao_contexto

    @pytest.mark.asyncio
    async def test_encerra_sessao_inexistente_nao_erro(self):
        svc = AIService.__new__(AIService)
        svc._lock = asyncio.Lock()
        svc._sessoes = OrderedDict()
        svc._sessao_contexto = {}

        await svc.encerrar_sessao("conv-x")


# ---------------------------------------------------------------------------
# _construir_prompt_educacional
# ---------------------------------------------------------------------------

class TestConstruirPromptEducacional:
    def test_prompt_contem_tema_e_perfil(self):
        svc = AIService.__new__(AIService)
        perfil = {
            "nivel_atencao": "médio",
            "dificuldade_leitura": True,
            "preferencia": "visual",
            "interesses": "arte",
            "diagnostico": "dislexia",
        }
        prompt = svc._construir_prompt_educacional("Fotosíntese", perfil)
        assert "Fotosíntese" in prompt
        assert "médio" in prompt
        assert "Sim" in prompt
        assert "visual" in prompt
        assert "arte" in prompt
        assert "dislexia" in prompt

    def test_prompt_campos_ausentes_usa_default(self):
        svc = AIService.__new__(AIService)
        prompt = svc._construir_prompt_educacional("Matemática", {})
        assert "não informado" in prompt
        assert "Não" in prompt

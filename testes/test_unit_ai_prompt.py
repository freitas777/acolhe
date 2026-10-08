"""
CT10 - Prompt educacional inclui todos os campos do perfil
Tipo: Teste unitario (service)
Estrategia: Desabilitar a inicializacao do modelo Gemini, montar o prompt
com um perfil completo e verificar que todos os campos estao presentes.
"""
import pytest
from unittest.mock import MagicMock


class TestAIServicePrompt:

    def test_CT10_prompt_educacional_inclui_todos_os_campos(self, monkeypatch):
        # Arrange - desabilitar inicializacao do Gemini
        import backend.services.ai_service as ai_mod
        monkeypatch.setattr(ai_mod.settings, "gemini_api_key", "")

        from backend.services.prompt_builder import prompt_builder

        perfil = MagicMock()
        perfil.nivel_atencao = MagicMock()
        perfil.nivel_atencao.value = "alto"
        perfil.dificuldade_leitura = True
        perfil.preferencia = MagicMock()
        perfil.preferencia.value = "visual"
        perfil.interesses = "jogos e musica"
        perfil.diagnostico = "TEA"

        aluno = MagicMock()
        aluno.nome = "Aluno Teste"
        aluno.observacoes = ""

        # Act
        prompt = prompt_builder.build_student_profile(aluno, perfil)

        # Assert
        assert "alto" in prompt
        assert "Sim" in prompt
        assert "visual" in prompt
        assert "jogos e musica" in prompt
        assert "TEA" in prompt


class TestAIServiceCompaction:

    def test_recriar_sessao_insere_resumo_e_janela_recente(self, monkeypatch):
        # Arrange - desabilitar inicializacao do Gemini
        import backend.services.ai_service as ai_mod
        monkeypatch.setattr(ai_mod.settings, "gemini_api_key", "")

        from backend.services.ai_service import AIService
        service = AIService()

        model_mock = MagicMock()
        service._model = model_mock
        service._sessoes = {}

        def _msg(papel, conteudo):
            m = MagicMock()
            m.papel = papel
            m.conteudo = conteudo
            return m

        mensagens = [_msg("usuario", f"pergunta {i}") for i in range(20)]

        # Act
        service._recriar_sessao("conv1", system_instruction="INSTRUCAO", mensagens=mensagens)

        # Assert
        assert "conv1" in service._sessoes
        model_mock.start_chat.assert_called_once()
        history = model_mock.start_chat.call_args.kwargs["history"]

        parts_texts = [p["parts"][0] for p in history]
        assert any("RESUMO DAS MENSAGENS ANTERIORES" in t for t in parts_texts)

        # Janela: base (2) + resumo (2) + ultimas MENSAGENS_RECENTES
        from backend.services.ai_service import MENSAGENS_RECENTES
        assert len(history) == 2 + 2 + MENSAGENS_RECENTES

    def test_resumir_antigas_trunca_tamanho(self, monkeypatch):
        import backend.services.ai_service as ai_mod
        monkeypatch.setattr(ai_mod.settings, "gemini_api_key", "")

        from backend.services.ai_service import AIService, MAX_RESUMO_CHARS
        service = AIService()

        def _msg(conteudo):
            m = MagicMock()
            m.conteudo = conteudo
            return m

        mensagens = [_msg("x" * 300) for _ in range(20)]

        resumo = service._resumir_antigas(mensagens)

        assert isinstance(resumo, str)
        assert len(resumo) <= MAX_RESUMO_CHARS + len("\n...[resumo truncado]")

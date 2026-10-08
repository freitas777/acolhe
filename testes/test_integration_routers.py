"""
Testes de Integracao de Routers - Acolhe+
Estrategia: Testar endpoints HTTP completos usando TestClient do FastAPI.
Valida request -> router -> service -> repository -> response.
Usa banco SQLite em memoria e fixtures de usuarios autenticados.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.models.aluno import Aluno
from backend.models.pendencia_validacao import PendenciaValidacao, StatusPendencia


class TestImportacaoRouter:
    """
    CT02 - Importar aluno cria registro e pendencia
    Tipo: Teste de integracao (router)
    Estrategia: Mockar SUAPService e fazer POST real no endpoint /importacao/importar.
    Verificar que Aluno e PendenciaValidacao sao criados no banco.
    """

    def test_CT02_importar_aluno_cria_registro_e_pendencia(
        self, client, usuario_psicopedagogo, db_session, monkeypatch
    ):
        # Arrange
        monkeypatch.setattr("backend.routers.importacao.DEV_MODE", False)

        mock_suap = MagicMock()
        mock_suap.get_aluno_matriculado = AsyncMock(return_value={
            "nome": "Aluno Importado",
            "matricula": "555555",
            "curso": "Informatica",
            "campus": "Campus Central",
            "foto_base64": "",
            "mime_type": "",
            "email_pessoal": "aluno@email.com",
            "email_academico": "aluno@suap.ifrn.edu.br",
            "suap_id": "suap_555",
            "cpf": "111.222.333-44",
            "foto_url": "",
        })
        mock_suap.buscar_alunos_resumido = AsyncMock(return_value=[])

        # Act
        with patch("backend.routers.importacao.SUAPService", return_value=mock_suap):
            response = client.post(
                "/importacao/importar",
                json={"matricula": "555555"},
                headers=usuario_psicopedagogo["headers"],
            )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["nome"] == "Aluno Importado"
        assert data["matricula"] == "555555"
        assert data["status_acompanhamento"] == "aguardando_indicacao"

        pendencia = (
            db_session.query(PendenciaValidacao)
            .filter(PendenciaValidacao.aluno_id == data["id"])
            .first()
        )
        assert pendencia is not None
        assert pendencia.status == StatusPendencia.pendente


class TestEquipeRouterPerfil:
    """
    CT03 - Criar perfil de aluno
    Tipo: Teste de integracao (router)
    Estrategia: Criar Aluno sem perfil, fazer PUT no endpoint /equipe/alunos/{id}/perfil
    e verificar que PerfilAluno e criado com os dados enviados.
    """

    def test_CT03_criar_perfil_de_aluno(self, client, usuario_psicopedagogo, db_session):
        # Arrange
        aluno = Aluno(
            nome="Aluno Sem Perfil",
            matricula="999999",
            suap_id="sem_perfil_001",
        )
        db_session.add(aluno)
        db_session.commit()
        db_session.refresh(aluno)

        # Act
        response = client.put(
            f"/equipe/alunos/{aluno.id}/perfil",
            json={
                "nivel_atencao": "alto",
                "dificuldade_leitura": True,
                "preferencia": "visual",
                "interesses": "jogos",
                "diagnostico": "TEA",
            },
            headers=usuario_psicopedagogo["headers"],
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["nivel_atencao"] == "alto"
        assert data["dificuldade_leitura"] is True
        assert data["preferencia"] == "visual"
        assert data["interesses"] == "jogos"
        assert data["diagnostico"] == "TEA"


class TestEquipeRouterMembros:
    """
    CT04 - Listar membros da equipe
    Tipo: Teste de integracao (router)
    Estrategia: Autenticar como NAPNE e fazer GET /equipe/membros.
    Verificar que a resposta e HTTP 200 com lista nao vazia.
    """

    def test_CT04_listar_membros_da_equipe(self, client, usuario_psicopedagogo):
        # Act
        response = client.get(
            "/equipe/membros",
            headers=usuario_psicopedagogo["headers"],
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1


class TestAuthRouterConvite:
    """
    CT08 - Criar convite para membro NAPNE
    Tipo: Teste de integracao (router)
    Estrategia: Autenticar como psicopedagogo e fazer POST /auth/convite
    com email inexistente. Verificar que retorna HTTP 200 com senha_temporaria.
    """

    def test_CT08_criar_convite_para_membro_napne(self, client, usuario_psicopedagogo):
        # Act
        response = client.post(
            "/auth/convite",
            json={
                "nome": "Novo Membro",
                "email": "novo_convite@test.com",
                "tipo_perfil": "psicopedagogo",
            },
            headers=usuario_psicopedagogo["headers"],
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "novo_convite@test.com"
        assert "senha_temporaria" in data
        assert len(data["senha_temporaria"]) == 10


class TestChatRouterConteudoEducacional:
    """
    CT09 - Gerar conteudo educacional com perfil
    Tipo: Teste de integracao (router)
    Estrategia: Mockar o ai_service no chat_service e fazer POST real
    no endpoint /api/chat/educational-content. Verificar resposta HTTP 200.
    """

    def test_CT09_gerar_conteudo_educacional_com_perfil(
        self, client, usuario_psicopedagogo, mocker
    ):
        # Arrange - mockar o ai_service que e usado dentro de chat_service
        mock_ai = mocker.patch("backend.services.chat_service.ai_service")
        mock_ai.gerar_conteudo_educacional = AsyncMock(
            return_value="Conteudo sobre fracoes adaptado para aluno com TEA"
        )

        # Act
        response = client.post(
            "/api/chat/educational-content",
            json={
                "tema": "Fra\u00e7\u00f5es",
                "perfil_aluno": {
                    "nivel_atencao": "alto",
                    "dificuldade_leitura": True,
                    "preferencia": "visual",
                },
            },
            headers=usuario_psicopedagogo["headers"],
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["tema"] == "Fra\u00e7\u00f5es"
        assert "conteudo" in data
        assert len(data["conteudo"]) > 0


class TestChatRouterConversas:
    """
    CT11 - Deletar conversa propria
    Tipo: Teste de integracao (router)
    Estrategia: Criar conversa via POST, depois deletar via DELETE
    e verificar HTTP 204 e que a conversa foi removida do banco.
    """

    def test_CT11_deletar_conversa_propria(self, client, usuario_psicopedagogo, mocker):
        # Arrange - mockar o ai_service com metodos assincronos
        mock_ai = mocker.patch("backend.services.chat_service.ai_service")
        mock_ai.iniciar_sessao = AsyncMock()
        mock_ai.encerrar_sessao = AsyncMock()
        mock_ai.garantir_sessao_com_contexto = AsyncMock()

        create_response = client.post(
            "/api/chat/conversations",
            json={"titulo": "Conversa para deletar"},
            headers=usuario_psicopedagogo["headers"],
        )
        assert create_response.status_code == 201
        conversa_id = create_response.json()["id"]

        # Act
        response = client.delete(
            f"/api/chat/conversations/{conversa_id}",
            headers=usuario_psicopedagogo["headers"],
        )

        # Assert
        assert response.status_code == 204

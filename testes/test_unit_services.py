"""
Testes Unitarios de Services - Acolhe+
Estrategia: Testar logica de negocio isolada, mockando dependencias externas (SUAP, IA).
Usa o padrao AAA (Arrange, Act, Assert) e banco SQLite em memoria.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from backend.services.auth_service import AuthService
from backend.models.aluno import Aluno
from backend.models.pendencia_validacao import PendenciaValidacao
from backend.models.pendencia_validacao import StatusPendencia


class TestAuthServiceLoginSUAP:
    """
    CT01 - Login SUAP cria usuario novo
    Tipo: Teste unitario (service)
    Estrategia: Mockar SUAPService para retornar dados validos e verificar
    que AuthService cria um novo registro de Usuario no banco.
    """

    @pytest.mark.asyncio
    async def test_CT01_login_suap_cria_usuario_novo(self, db_session, mocker):
        # Arrange
        mock_suap = mocker.patch("backend.services.auth_service.SUAPService")
        mock_instance = mock_suap.return_value
        mock_instance.get_eu = AsyncMock(return_value={
            "identificacao": "999999",
            "nome_usual": "Novo Usuario",
            "email": "novo@test.com",
            "campus": "Campus Teste",
        })
        mock_instance.get_meus_vinculos = AsyncMock(return_value=[{
            "identificador": "2024001",
            "tipo": "aluno",
            "campus": "Campus Teste",
            "detalhamento": {"cargo": ""},
        }])
        mock_instance.buscar_alunos_resumido = AsyncMock(return_value=[])
        mock_instance.get_disciplinas = AsyncMock(return_value=[])

        service = AuthService(db_session)

        # Act
        resultado = await service.login_com_suap("token_valido", "2026.1")

        # Assert
        assert resultado is not None
        assert resultado["usuario"].suap_id == "999999"
        assert resultado["usuario"].nome == "Novo Usuario"
        assert resultado["usuario"].email == "novo@test.com"
        assert resultado["tipo_perfil"] == "aluno"


class TestAuthServicePendencias:
    """
    CT05 - Validar pendencia aprova aluno
    CT06 - Validar pendencia rejeita aluno
    Tipo: Teste unitario (service)
    Estrategia: Criar Aluno e PendenciaValidacao diretamente no banco,
    chamar AuthService.validar_pendencia e verificar que o status do
    aluno mudou para "ativo" (CT05) ou "rejeitado" (CT06).
    """

    def test_CT05_validar_pendencia_aprova_aluno(self, db_session, usuario_psicopedagogo):
        # Arrange
        aluno = Aluno(
            nome="Aluno Pendente",
            matricula="PEND001",
            suap_id="pend_001",
            status_acompanhamento="aguardando_indicacao",
        )
        db_session.add(aluno)
        db_session.commit()
        db_session.refresh(aluno)

        pendencia = PendenciaValidacao(
            aluno_id=aluno.id,
            indicado_por_id=usuario_psicopedagogo["usuario"].id,
            motivo="Teste CT062",
            status=StatusPendencia.pendente,
        )
        db_session.add(pendencia)
        db_session.commit()
        db_session.refresh(pendencia)

        service = AuthService(db_session)

        # Act
        resultado = service.validar_pendencia(
            pendencia.id,
            usuario_psicopedagogo["usuario"].id,
            StatusPendencia.validado.value,
        )

        # Assert
        assert resultado.status == StatusPendencia.validado
        assert resultado.validado_por_id == usuario_psicopedagogo["usuario"].id
        db_session.refresh(aluno)
        assert aluno.status_acompanhamento == "ativo"

    def test_CT06_validar_pendencia_rejeita_aluno(self, db_session, usuario_psicopedagogo):
        # Arrange
        aluno = Aluno(
            nome="Aluno A Rejeitar",
            matricula="REJCT06",
            suap_id="rej_ct06",
            status_acompanhamento="aguardando_indicacao",
        )
        db_session.add(aluno)
        db_session.commit()
        db_session.refresh(aluno)

        pendencia = PendenciaValidacao(
            aluno_id=aluno.id,
            indicado_por_id=usuario_psicopedagogo["usuario"].id,
            motivo="Teste CT06",
            status=StatusPendencia.pendente,
        )
        db_session.add(pendencia)
        db_session.commit()
        db_session.refresh(pendencia)

        service = AuthService(db_session)

        # Act
        resultado = service.validar_pendencia(
            pendencia.id,
            usuario_psicopedagogo["usuario"].id,
            StatusPendencia.rejeitado.value,
        )

        # Assert
        assert resultado.status == StatusPendencia.rejeitado
        assert resultado.validado_por_id == usuario_psicopedagogo["usuario"].id
        db_session.refresh(aluno)
        assert aluno.status_acompanhamento == "rejeitado"


class TestAuthServiceAlunosAtivos:
    """
    CT07 - Obter alunos ativos
    Tipo: Teste unitario (service)
    Estrategia: Criar alunos com diferentes status no banco e verificar
    que obter_alunos_ativos retorna apenas os com status "ativo".
    """

    def test_CT07_obter_alunos_ativos(self, db_session):
        # Arrange
        ativo1 = Aluno(
            nome="Aluno Ativo 1",
            matricula="AT001",
            suap_id="at_001",
            status_acompanhamento="ativo",
        )
        ativo2 = Aluno(
            nome="Aluno Ativo 2",
            matricula="AT002",
            suap_id="at_002",
            status_acompanhamento="ativo",
        )
        inativo = Aluno(
            nome="Aluno Rejeitado",
            matricula="REJ001",
            suap_id="rej_001",
            status_acompanhamento="rejeitado",
        )
        aguardando = Aluno(
            nome="Aluno Aguardando",
            matricula="AGU001",
            suap_id="agu_001",
            status_acompanhamento="aguardando_indicacao",
        )
        db_session.add_all([ativo1, ativo2, inativo, aguardando])
        db_session.commit()

        service = AuthService(db_session)

        # Act
        ativos = service.obter_alunos_ativos()

        # Assert
        assert len(ativos) >= 2
        assert all(a.status_acompanhamento == "ativo" for a in ativos)
        nomes = [a.nome for a in ativos]
        assert "Aluno Ativo 1" in nomes
        assert "Aluno Ativo 2" in nomes
        assert "Aluno Rejeitado" not in nomes
        assert "Aluno Aguardando" not in nomes

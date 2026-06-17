from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from backend.services.suap_service import SUAPService


def _make_response(json_data, status_code=200):
    response = MagicMock(spec=httpx.Response)
    response.json.return_value = json_data
    response.status_code = status_code
    response.raise_for_status = MagicMock()
    if status_code >= 400:
        error = httpx.HTTPStatusError(
            message="error", request=MagicMock(), response=response,
        )
        response.raise_for_status.side_effect = error
    return response


def _make_http_error(status_code: int):
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    return httpx.HTTPStatusError(
        message="error", request=MagicMock(), response=response,
    )


@pytest.fixture
def svc():
    with patch.object(SUAPService, "__init__", lambda self: None):
        s = SUAPService()
    s.base_url = "https://suap.test"
    return s


class TestGet:
    @pytest.mark.asyncio
    async def test_get_sends_bearer_token(self, svc):
        response = _make_response({"ok": True})
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        with patch("backend.services.suap_service.httpx.AsyncClient", return_value=mock_client):
            result = await svc._get("tok123", "/api/test/")
        mock_client.get.assert_called_once_with(
            "https://suap.test/api/test/",
            params=None,
            headers={"Authorization": "Bearer tok123", "Accept": "application/json"},
        )
        response.raise_for_status.assert_called_once()
        assert result is response

    @pytest.mark.asyncio
    async def test_get_passes_params(self, svc):
        response = _make_response({"ok": True})
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        with patch("backend.services.suap_service.httpx.AsyncClient", return_value=mock_client):
            await svc._get("tok", "/api/test/", params={"page": 2})
        mock_client.get.assert_called_once()
        call_kwargs = mock_client.get.call_args
        assert call_kwargs[1]["params"] == {"page": 2}


class TestGetMeusDados:
    @pytest.mark.asyncio
    async def test_returns_json(self, svc):
        expected = {"nome": "Joao", "matricula": "123"}
        with patch.object(svc, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _make_response(expected)
            result = await svc.get_meus_dados("tok")
        mock_get.assert_called_once_with("tok", "/api/rh/meus-dados/")
        assert result == expected


class TestGetEu:
    @pytest.mark.asyncio
    async def test_returns_json(self, svc):
        expected = {"id": 1, "nome": "Maria"}
        with patch.object(svc, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _make_response(expected)
            result = await svc.get_eu("tok")
        mock_get.assert_called_once_with("tok", "/api/rh/eu/")
        assert result == expected


class TestGetMeusVinculos:
    @pytest.mark.asyncio
    async def test_single_page(self, svc):
        data = {"results": [{"id": 1}], "next": None}
        with patch.object(svc, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _make_response(data)
            result = await svc.get_meus_vinculos("tok")
        assert result == [{"id": 1}]
        mock_get.assert_called_once_with("tok", "/api/rh/meus-vinculos/", params={"page": 1})

    @pytest.mark.asyncio
    async def test_pagination(self, svc):
        page1 = {"results": [{"id": 1}], "next": "http://suap/?page=2"}
        page2 = {"results": [{"id": 2}], "next": None}
        with patch.object(svc, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [_make_response(page1), _make_response(page2)]
            result = await svc.get_meus_vinculos("tok")
        assert result == [{"id": 1}, {"id": 2}]
        assert mock_get.call_count == 2
        mock_get.assert_any_call("tok", "/api/rh/meus-vinculos/", params={"page": 1})
        mock_get.assert_any_call("tok", "/api/rh/meus-vinculos/", params={"page": 2})


class TestGetDisciplinas:
    @pytest.mark.asyncio
    async def test_list_response(self, svc):
        data = [{"id": 1}, {"id": 2}]
        with patch.object(svc, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _make_response(data)
            result = await svc.get_disciplinas("tok", "2026.1")
        assert result == [{"id": 1}, {"id": 2}]

    @pytest.mark.asyncio
    async def test_dict_response_with_results(self, svc):
        data = {"results": [{"id": 1}]}
        with patch.object(svc, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _make_response(data)
            result = await svc.get_disciplinas("tok", "2026.1")
        assert result == [{"id": 1}]

    @pytest.mark.asyncio
    async def test_passes_semestre_in_path(self, svc):
        with patch.object(svc, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _make_response([])
            await svc.get_disciplinas("tok", "2025.2")
        mock_get.assert_called_once_with("tok", "/api/ensino/disciplinas/2025.2/")


class TestGetMeusDiarios:
    @pytest.mark.asyncio
    async def test_pagination(self, svc):
        page1 = {"results": [{"id": 10}], "next": "http://suap/?page=2"}
        page2 = {"results": [{"id": 20}], "next": None}
        with patch.object(svc, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [_make_response(page1), _make_response(page2)]
            result = await svc.get_meus_diarios("tok", 2026, 1)
        assert result == [{"id": 10}, {"id": 20}]

    @pytest.mark.asyncio
    async def test_passes_ano_periodo_in_path(self, svc):
        with patch.object(svc, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _make_response({"results": [], "next": None})
            await svc.get_meus_diarios("tok", 2025, 2)
        mock_get.assert_called_once_with("tok", "/api/ensino/meus-diarios/2025/2/", params={"page": 1})


class TestGetAlunosDiario:
    @pytest.mark.asyncio
    async def test_single_page(self, svc):
        data = {"results": [{"matricula": "111"}], "next": None}
        with patch.object(svc, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _make_response(data)
            result = await svc.get_alunos_diario("tok", 42)
        assert result == [{"matricula": "111"}]
        mock_get.assert_called_once_with("tok", "/api/ensino/diarios/42/alunos/", params={"page": 1})


class TestGetAlunoMatriculado:
    @pytest.mark.asyncio
    async def test_found(self, svc):
        expected = {"matricula": "123", "nome": "Joao"}
        with patch.object(svc, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _make_response(expected)
            result = await svc.get_aluno_matriculado("tok", "123")
        assert result == expected
        mock_get.assert_called_once_with("tok", "/api/ensino/aluno-matriculado/", params={"matricula": "123"})

    @pytest.mark.asyncio
    async def test_not_found_returns_none(self, svc):
        with patch.object(svc, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = _make_http_error(404)
            result = await svc.get_aluno_matriculado("tok", "999")
        assert result is None

    @pytest.mark.asyncio
    async def test_other_error_propagates(self, svc):
        with patch.object(svc, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = _make_http_error(500)
            with pytest.raises(httpx.HTTPStatusError):
                await svc.get_aluno_matriculado("tok", "123")


class TestBuscarAlunosResumido:
    @pytest.mark.asyncio
    async def test_with_no_filters(self, svc):
        data = [{"matricula": "1"}]
        with patch.object(svc, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _make_response(data)
            result = await svc.buscar_alunos_resumido("tok")
        assert result == [{"matricula": "1"}]
        mock_get.assert_called_once_with("tok", "/api/ensino/aluno-resumido/", params={}, timeout=20.0)

    @pytest.mark.asyncio
    async def test_with_all_filters(self, svc):
        data = {"results": [{"matricula": "1"}]}
        with patch.object(svc, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _make_response(data)
            result = await svc.buscar_alunos_resumido("tok", matricula="123", codigo_curso="C1", ano_conclusao="2024")
        assert result == [{"matricula": "1"}]
        call_kwargs = mock_get.call_args
        assert call_kwargs[1]["params"] == {"matricula": "123", "codigo_curso": "C1", "ano_conclusao": "2024"}

    @pytest.mark.asyncio
    async def test_not_found_returns_empty_list(self, svc):
        with patch.object(svc, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = _make_http_error(404)
            result = await svc.buscar_alunos_resumido("tok")
        assert result == []

    @pytest.mark.asyncio
    async def test_other_error_propagates(self, svc):
        with patch.object(svc, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = _make_http_error(500)
            with pytest.raises(httpx.HTTPStatusError):
                await svc.buscar_alunos_resumido("tok")

    @pytest.mark.asyncio
    async def test_list_response(self, svc):
        data = [{"matricula": "1"}, {"matricula": "2"}]
        with patch.object(svc, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _make_response(data)
            result = await svc.buscar_alunos_resumido("tok")
        assert result == [{"matricula": "1"}, {"matricula": "2"}]


class TestValidarToken:
    @pytest.mark.asyncio
    async def test_valid(self, svc):
        with patch.object(svc, "get_meus_dados", new_callable=AsyncMock) as mock:
            mock.return_value = {"nome": "ok"}
            result = await svc.validar_token("good-tok")
        assert result is True

    @pytest.mark.asyncio
    async def test_invalid(self, svc):
        with patch.object(svc, "get_meus_dados", new_callable=AsyncMock) as mock:
            mock.side_effect = _make_http_error(401)
            result = await svc.validar_token("bad-tok")
        assert result is False

import httpx
import pytest

from app.services.supabase_rest import SupabaseRestService


@pytest.mark.asyncio
async def test_supabase_rest_reads_env_and_queries_channel_and_ia_config(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://supabase.alfaia.test")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-role-test")

    requested = []

    async def handler(request: httpx.Request):
        requested.append((request.method, str(request.url), dict(request.headers)))
        assert request.headers["apikey"] == "service-role-test"
        assert request.headers["Authorization"] == "Bearer service-role-test"

        url = str(request.url)
        if "/rest/v1/canais" in url:
            assert "uazapi_token=eq.token%2F123" in url
            return httpx.Response(
                200,
                json=[
                    {
                        "id": "canal-1",
                        "tenant_id": "tenant-1",
                        "uazapi_instancia": "loja-centro",
                        "uazapi_token": "token/123",
                    }
                ],
            )

        if "/rest/v1/ia_config" in url:
            assert "tenant_id=eq.tenant-1" in url
            return httpx.Response(
                200,
                json=[
                    {
                        "tenant_id": "tenant-1",
                        "modelo": "openai/gpt-4o-mini",
                        "prompt_sistema": "Prompt QA",
                    }
                ],
            )

        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        service = SupabaseRestService(httpx_client=http_client)
        canal = await service.buscar_canal_por_token("token/123")
        config = await service.buscar_ia_config("tenant-1")

    assert canal["uazapi_instancia"] == "loja-centro"
    assert config["modelo"] == "openai/gpt-4o-mini"
    assert [item[0] for item in requested] == ["GET", "GET"]


@pytest.mark.asyncio
async def test_supabase_rest_without_service_role_does_not_call_http(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://supabase.alfaia.test")
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_KEY", raising=False)

    async def handler(request: httpx.Request):
        raise AssertionError("Supabase nao deveria ser chamado sem service role.")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        service = SupabaseRestService(httpx_client=http_client)
        canal = await service.buscar_canal_por_token("token/123")

    assert canal is None

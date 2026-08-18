import json

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


@pytest.mark.asyncio
async def test_supabase_rest_identifica_lead_conversa_historico_e_registra_mensagem(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://supabase.alfaia.test")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-role-test")

    calls = []

    async def handler(request: httpx.Request):
        calls.append((request.method, str(request.url), dict(request.headers), request.content))
        assert request.headers["apikey"] == "service-role-test"
        assert request.headers["Authorization"] == "Bearer service-role-test"

        url = str(request.url)
        if "/rest/v1/rpc/identificar_lead" in url:
            body = json.loads(request.content.decode("utf-8"))
            assert body == {
                "p_tenant": "tenant-1",
                "p_telefone": "558599173321",
                "p_push_name": "Valmir Junior",
                "p_origem": "whatsapp_organico",
            }
            return httpx.Response(
                200,
                json={
                    "contato_id": "contato-1",
                    "lead_id": "lead-1",
                    "entrada": "continuacao",
                },
            )

        if "/rest/v1/conversas" in url:
            assert "on_conflict=tenant_id,contato_id" in url
            assert request.headers["Prefer"] == "resolution=merge-duplicates,return=representation"
            body = json.loads(request.content.decode("utf-8"))
            assert body["tenant_id"] == "tenant-1"
            assert body["contato_id"] == "contato-1"
            assert body["lead_id"] == "lead-1"
            assert body["canal_id"] == "canal-1"
            assert body["estado"] == "ia"
            return httpx.Response(201, json=[{"id": "conversa-1"}])

        if "/rest/v1/mensagens?select=" in url:
            assert "conversa_id=eq.conversa-1" in url
            return httpx.Response(
                200,
                json=[
                    {
                        "id": "msg-1",
                        "remetente": "lead",
                        "texto": "Oi",
                        "enviado_em": "2026-08-17T12:00:00+00:00",
                    }
                ],
            )

        if "/rest/v1/rpc/registrar_mensagem_idempotente" in url:
            body = json.loads(request.content.decode("utf-8"))
            assert body["p_payload"]["wa_message_id"] == "wamid.real.uazapi.001"
            assert body["p_payload"]["conversa_id"] == "conversa-1"
            return httpx.Response(204)

        if "/rest/v1/mensagens?on_conflict=wa_message_id" in url:
            raise AssertionError("registrar_mensagem nao deve usar on_conflict REST contra indice parcial.")

        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        service = SupabaseRestService(httpx_client=http_client)
        identidade = await service.identificar_lead("tenant-1", "558599173321", "Valmir Junior")
        conversa = await service.upsert_conversa("tenant-1", "contato-1", "lead-1", "canal-1")
        historico = await service.buscar_historico_mensagens("conversa-1")
        await service.registrar_mensagem({
            "tenant_id": "tenant-1",
            "conversa_id": "conversa-1",
            "wa_message_id": "wamid.real.uazapi.001",
            "texto": "Oi",
        })

    assert identidade["contato_id"] == "contato-1"
    assert conversa["id"] == "conversa-1"
    assert historico[0]["texto"] == "Oi"
    assert [item[0] for item in calls] == ["POST", "POST", "GET", "POST"]

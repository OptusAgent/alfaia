import json

import pytest

from app.adapters.base import PayloadNormalizado, ResultadoEnvio
from app.routers import webhooks


@pytest.mark.asyncio
async def test_webhook_resolves_channel_fetches_ia_config_and_sends_with_real_instance(monkeypatch):
    calls = {
        "canal_token": None,
        "ia_tenant": None,
        "registered": [],
        "adapter_init": None,
        "sent": None,
        "ia_config": None,
    }

    class FakeSupabase:
        async def buscar_canal_por_token(self, token):
            calls["canal_token"] = token
            return {
                "id": "canal-123",
                "tenant_id": "tenant-123",
                "uazapi_base_url": "https://uazapi.alfaia.test",
                "uazapi_instancia": "loja-centro",
                "uazapi_token": "token-real-instancia",
            }

        async def buscar_ia_config(self, tenant_id):
            calls["ia_tenant"] = tenant_id
            return {
                "tenant_id": tenant_id,
                "modelo": "openai/gpt-4o-mini",
                "prompt_sistema": "Prompt do banco",
            }

        async def registrar_mensagem(self, payload):
            calls["registered"].append(payload)

    class FakeAdapter:
        def __init__(self, base_url, instance_name, token, **kwargs):
            calls["adapter_init"] = {
                "base_url": base_url,
                "instance_name": instance_name,
                "token": token,
            }

        def normalizar_webhook(self, raw, headers):
            return [
                PayloadNormalizado(
                    tenant_id="fallback-tenant",
                    canal_id="fallback-canal",
                    provider="uazapi",
                    telefone="5585988124477",
                    push_name="Mariana",
                    mensagem="Oi, quero agendar uma prova",
                    wa_message_id="wamid.qa.webhook",
                    timestamp=1786900000,
                    data_atual="2026-08-17",
                )
            ]

        async def enviar_texto(self, to, text):
            calls["sent"] = {"to": to, "text": text}
            return ResultadoEnvio(sucesso=True, wa_message_id="wamid.qa.sent")

    class FakeAI:
        def processar_atendimento(self, **kwargs):
            calls["ia_config"] = kwargs["ia_config"]
            assert kwargs["tenant_id"] == "tenant-123"
            assert kwargs["lead_dto"].contato_id == "contato_5585988124477"
            return type("AIResult", (), {"texto_resposta": "Resposta via OpenRouter mockada."})()

    monkeypatch.setattr(webhooks, "supabase_rest_service", FakeSupabase())
    monkeypatch.setattr(webhooks, "UazapiAdapter", FakeAdapter)
    monkeypatch.setattr(webhooks, "ai_engine_service", FakeAI())

    raw = json.dumps(
        {
            "wa_message_id": "wamid.qa.webhook",
            "event": "message.received",
            "telefone": "85988124477",
            "mensagem": "Oi, quero agendar uma prova",
        }
    ).encode("utf-8")

    await webhooks._processar_payload_background(
        provider="uazapi",
        raw_body=raw,
        headers={},
        token="token-webhook",
    )

    assert calls["canal_token"] == "token-webhook"
    assert calls["ia_tenant"] == "tenant-123"
    assert calls["adapter_init"] == {
        "base_url": "https://uazapi.alfaia.test",
        "instance_name": "loja-centro",
        "token": "token-real-instancia",
    }
    assert calls["ia_config"]["prompt_sistema"] == "Prompt do banco"
    assert calls["sent"] == {
        "to": "5585988124477",
        "text": "Resposta via OpenRouter mockada.",
    }
    assert calls["registered"][0]["canal_id"] == "canal-123"
    assert calls["registered"][1]["status"] == "enviado"


def test_webhook_required_env_blocks_missing_production_secret(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("UAZAPI_ADMIN_TOKEN", raising=False)

    with pytest.raises(RuntimeError, match="UAZAPI_ADMIN_TOKEN"):
        webhooks._required_env("UAZAPI_ADMIN_TOKEN")


def test_webhook_required_env_allows_dev_fallback(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("UAZAPI_ADMIN_TOKEN", raising=False)

    assert webhooks._required_env("UAZAPI_ADMIN_TOKEN", "dev-token") == "dev-token"

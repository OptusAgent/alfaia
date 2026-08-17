import json
import pytest
import httpx
from app.adapters.base import CanalAdapter, PayloadNormalizado
from app.adapters.uazapi import UazapiAdapter


def test_uazapi_capabilities():
    """Testa se as capacidades operacionais do UazapiAdapter correspondem ao PRD §14.1."""
    adapter = UazapiAdapter(delay_min_ms=1000, delay_max_ms=3000)
    assert isinstance(adapter, CanalAdapter)
    caps = adapter.capabilities
    assert caps.janela_24h is False
    assert caps.suporta_template is True
    assert caps.requer_delay is True
    assert caps.delay_min_ms == 1000
    assert caps.delay_max_ms == 3000


def test_uazapi_normalizar_webhook():
    """Testa normalização do webhook cru da UAZAPI no contrato de §6.3."""
    adapter = UazapiAdapter()
    raw_payload = json.dumps({
        "event": "message.received",
        "telefone": "(85) 98812-4477",
        "push_name": "Marcela Prado",
        "mensagem": "Quero alugar um vestido para dia 15",
        "wa_message_id": "wamid.UAZAPI12345",
        "timestamp": 1754570000,
        "tenant_id": "11111111-1111-1111-1111-111111111111",
        "canal_id": "22222222-2222-2222-2222-222222222222",
    }).encode("utf-8")

    normalized = adapter.normalizar_webhook(raw_payload, {})
    assert len(normalized) == 1
    p: PayloadNormalizado = normalized[0]
    assert p.provider == "uazapi"
    assert p.telefone == "5585988124477"
    assert p.push_name == "Marcela Prado"
    assert p.mensagem == "Quero alugar um vestido para dia 15"
    assert p.wa_message_id == "wamid.UAZAPI12345"


def test_uazapi_normalizar_webhook_payload_aninhado_remote_jid():
    adapter = UazapiAdapter()
    raw_payload = json.dumps({
        "event": "messages",
        "data": {
            "pushName": "Mariana",
            "messageTimestamp": 1786900000,
            "key": {
                "id": "wamid.remote_nested",
                "remoteJid": "85988124477@s.whatsapp.net",
                "fromMe": False,
            },
            "message": {
                "conversation": "Oi, queria agendar uma prova",
            },
        },
    }).encode("utf-8")

    normalized = adapter.normalizar_webhook(raw_payload, {})

    assert len(normalized) == 1
    assert normalized[0].telefone == "5585988124477"
    assert normalized[0].push_name == "Mariana"
    assert normalized[0].mensagem == "Oi, queria agendar uma prova"
    assert normalized[0].wa_message_id == "wamid.remote_nested"


@pytest.mark.asyncio
async def test_uazapi_enviar_texto_headers():
    """Testa envio de texto encapsulando header 'token' (AC 1, 2)."""
    async def mock_handler(request: httpx.Request):
        if "/chat/presence" in str(request.url):
            return httpx.Response(200, json={"status": "ok"})
        assert request.headers["token"] == "token_uazapi_123"
        body = json.loads(request.content.decode("utf-8"))
        assert body["number"] == "5585988124477"
        assert body["text"] == "Olá via UAZAPI"
        return httpx.Response(200, json={"id": "wamid.uazapi_sent_001"})

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = UazapiAdapter(
            base_url="https://api.uazapi.com",
            instance_name="loja_centro",
            token="token_uazapi_123",
            delay_min_ms=0,
            delay_max_ms=0,
            httpx_client=client,
        )
        res = await adapter.enviar_texto("(85) 98812-4477", "Olá via UAZAPI")
        assert res.sucesso is True
        assert res.wa_message_id == "wamid.uazapi_sent_001"


@pytest.mark.asyncio
async def test_uazapi_enviar_midia_headers():
    """Testa envio de mídia encapsulando o header correto de mídia (AC 1, 2)."""
    async def mock_handler(request: httpx.Request):
        if "/chat/presence" in str(request.url):
            return httpx.Response(200, json={"status": "ok"})
        assert request.headers["apikey"] == "token_uazapi_123"
        body = json.loads(request.content.decode("utf-8"))
        assert body["mediaUrl"] == "https://example.com/foto.jpg"
        assert body["mediaType"] == "image"
        return httpx.Response(200, json={"id": "wamid.uazapi_media_002"})

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = UazapiAdapter(
            base_url="https://api.uazapi.com",
            instance_name="loja_centro",
            token="token_uazapi_123",
            delay_min_ms=0,
            delay_max_ms=0,
            httpx_client=client,
        )
        res = await adapter.enviar_midia(
            to="85988124477",
            url="https://example.com/foto.jpg",
            tipo="image",
            caption="Foto do vestido",
        )
        assert res.sucesso is True
        assert res.wa_message_id == "wamid.uazapi_media_002"


@pytest.mark.asyncio
async def test_uazapi_instance_create_connect_and_webhook():
    """Testa os métodos de gestão de instância e pareamento via QR Code (AC 6)."""
    async def mock_handler(request: httpx.Request):
        url_str = str(request.url)
        if "/instance/create" in url_str:
            body = json.loads(request.content.decode("utf-8"))
            assert body["name"] == "instancia_loja_01"
            return httpx.Response(201, json={"id": "inst_123", "token": "token_gerado_456"})
        elif "/instance/connect" in url_str:
            return httpx.Response(200, json={"status": "qrcode", "qrcode": "data:image/png;base64,iVBORw0KGgoAAAANSU..."})
        elif "/webhook/" in url_str:
            return httpx.Response(200, json={"status": "webhook_configured"})
        return httpx.Response(404)

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = UazapiAdapter(
            base_url="https://api.uazapi.com",
            instance_name="instancia_loja_01",
            token="token_admin_789",
            httpx_client=client,
        )

        # 1. Teste criar instância
        res_create = await adapter.criar_instancia("instancia_loja_01", "tenant_piloto_123")
        assert res_create["id"] == "inst_123"

        # 2. Teste conectar e obter QR Code
        res_connect = await adapter.conectar_instancia()
        assert res_connect["status"] == "qrcode"
        assert res_connect["qrcode"].startswith("data:image/png;base64")

        # 3. Teste configurar webhook
        res_webhook = await adapter.configurar_webhook("instancia_loja_01", "https://api.alfaia.app/webhook/uazapi/token_gerado_456")
        assert res_webhook["status"] == "webhook_configured"

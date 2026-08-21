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


def test_uazapi_normalizar_webhook_payload_uazapigo_case_variants():
    adapter = UazapiAdapter()
    raw_payload = json.dumps({
        "EventType": "messages",
        "Data": {
            "PushName": "Valmir",
            "MessageTimestamp": 1787008883,
            "Key": {
                "ID": "wamid.uazapigo.case",
                "RemoteJid": "8599173321@s.whatsapp.net",
                "FromMe": False,
            },
            "Message": {
                "Conversation": "Oi, teste real da automação",
            },
        },
    }).encode("utf-8")

    normalized = adapter.normalizar_webhook(raw_payload, {})

    assert len(normalized) == 1
    assert normalized[0].telefone == "558599173321"
    assert normalized[0].push_name == "Valmir"
    assert normalized[0].mensagem == "Oi, teste real da automação"
    assert normalized[0].wa_message_id == "wamid.uazapigo.case"


def test_uazapi_normalizar_webhook_payload_info_chat_extended_text():
    adapter = UazapiAdapter()
    raw_payload = json.dumps({
        "EventType": "messages",
        "Data": {
            "PushName": "Valmir",
            "Info": {
                "ID": "wamid.info.chat",
                "Chat": "8599173321@s.whatsapp.net",
            },
            "Message": {
                "extendedTextMessage": {
                    "text": "Ainda nao respondeu pela automacao",
                },
            },
        },
    }).encode("utf-8")

    normalized = adapter.normalizar_webhook(raw_payload, {})

    assert len(normalized) == 1
    assert normalized[0].telefone == "558599173321"
    assert normalized[0].mensagem == "Ainda nao respondeu pela automacao"


def test_uazapi_normalizar_webhook_payload_sender_text_fallback():
    adapter = UazapiAdapter()
    raw_payload = json.dumps({
        "event": "messages",
        "message": {
            "sender": {
                "id": "8599173321@s.whatsapp.net",
                "name": "Valmir Junior",
            },
            "text": "Oi",
            "id": "wamid.sender.text",
        },
    }).encode("utf-8")

    normalized = adapter.normalizar_webhook(raw_payload, {})

    assert len(normalized) == 1
    assert normalized[0].telefone == "558599173321"
    assert normalized[0].mensagem == "Oi"


def test_uazapi_normalizar_webhook_payload_real_message_chatid_content():
    adapter = UazapiAdapter()
    raw_payload = json.dumps({
        "EventType": "messages",
        "chat": {
            "id": "558599173321@s.whatsapp.net",
            "name": "Valmir Junior",
        },
        "message": {
            "chatid": "558599173321@s.whatsapp.net",
            "senderName": "Valmir Junior",
            "content": "Tenho interesse em roupa para evento",
            "id": "3EB0REAL",
            "messageid": "wamid.real.uazapi.001",
        },
    }).encode("utf-8")

    normalized = adapter.normalizar_webhook(raw_payload, {})

    assert len(normalized) == 1
    assert normalized[0].telefone == "558599173321"
    assert normalized[0].push_name == "Valmir Junior"
    assert normalized[0].mensagem == "Tenho interesse em roupa para evento"
    assert normalized[0].wa_message_id == "wamid.real.uazapi.001"


def test_uazapi_normalizar_webhook_extrai_timestamp_ms_do_message_node():
    """Regressão: payload real da UAZAPI traz messageTimestamp (ms) dentro de
    `message`, não em `data`/top-level. Sem checar message_node, o parser caía
    no fallback fixo e toda mensagem de lead nascia com uma data de mais de um
    ano atrás, sumindo da ordenação da conversa no Portal."""
    adapter = UazapiAdapter()
    raw_payload = json.dumps({
        "EventType": "messages",
        "instanceName": "testealfaia",
        "message": {
            "chatid": "558591733321@s.whatsapp.net",
            "content": "Dia 25 de agosto",
            "fromMe": False,
            "messageTimestamp": 1787142609000,
            "messageid": "AC211B5267402B502F4AD15A4A421331",
            "senderName": "valmirmoreirajunior",
            "text": "Dia 25 de agosto",
        },
    }).encode("utf-8")

    normalized = adapter.normalizar_webhook(raw_payload, {})

    assert len(normalized) == 1
    assert normalized[0].timestamp == 1787142609


def test_uazapi_ignora_mensagem_enviada_pela_api_com_boolean_string():
    adapter = UazapiAdapter()
    raw_payload = json.dumps({
        "event": "messages",
        "data": {
            "wasSentByApi": "true",
            "key": {"remoteJid": "8599173321@s.whatsapp.net"},
            "message": {"conversation": "Eco da propria automacao"},
        },
    }).encode("utf-8")

    assert adapter.normalizar_webhook(raw_payload, {}) == []


def test_uazapi_diagnostico_nao_expoe_valores_de_payload():
    adapter = UazapiAdapter()
    raw_payload = json.dumps({
        "EventType": "messages",
        "Data": {
            "Info": {"Chat": "8599173321@s.whatsapp.net"},
            "Message": {"Conversation": "Texto secreto do cliente"},
        },
    }).encode("utf-8")

    diagnostico = adapter.diagnosticar_webhook(raw_payload)

    assert diagnostico["json_ok"] is True
    assert "Data.Info.Chat" in diagnostico["phone_candidate_paths"]
    assert "Data.Message.Conversation" in diagnostico["text_candidate_paths"]
    assert "Texto secreto do cliente" not in json.dumps(diagnostico)


@pytest.mark.asyncio
async def test_uazapi_presence_composing_usa_endpoint_correto():
    """
    Achado real em produção (2026-08-21, confirmado empiricamente contra optus.uazapi.com): o
    endpoint até então implementado, `POST /chat/presence/{instance}`, devolve HTTP 405 (esse path
    só aceita GET) — o "digitando..." nunca era enviado de fato, mas a exceção era engolida em
    silêncio (só logava, nunca propagava). O endpoint real é `POST /message/presence`, sem
    instância no path.
    """
    chamadas: list[httpx.Request] = []

    async def mock_handler(request: httpx.Request):
        chamadas.append(request)
        if "/message/presence" in str(request.url):
            return httpx.Response(200, json={"response": "Chat presence sent successfully"})
        return httpx.Response(200, json={"id": "wamid.001"})

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
        await adapter.enviar_presence_composing("5585988124477")

    assert len(chamadas) == 1
    req = chamadas[0]
    assert str(req.url) == "https://api.uazapi.com/message/presence"
    assert "/chat/presence" not in str(req.url)
    assert req.headers["token"] == "token_uazapi_123"
    body = json.loads(req.content.decode("utf-8"))
    assert body["number"] == "5585988124477"
    assert body["presence"] == "composing"


@pytest.mark.asyncio
async def test_uazapi_enviar_texto_headers():
    """Testa envio de texto encapsulando header 'token' (AC 1, 2)."""
    async def mock_handler(request: httpx.Request):
        if "/message/presence" in str(request.url):
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
        if "/message/presence" in str(request.url):
            return httpx.Response(200, json={"status": "ok"})
        assert request.headers["apikey"] == "token_uazapi_123"
        body = json.loads(request.content.decode("utf-8"))
        # Nomes de campo confirmados empiricamente contra a API real da UAZAPI (2026-08-21) —
        # não "mediaUrl"/"mediaType"/"caption" como assumido originalmente na story 2.3.
        assert body["file"] == "https://example.com/foto.jpg"
        assert body["type"] == "image"
        assert body["text"] == "Foto do vestido"
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


@pytest.mark.asyncio
async def test_uazapi_enviar_midia_retenta_em_falha_transitoria():
    """
    Regressão do achado real em produção (2026-08-21): uma falha transitória (timeout/exceção
    sem status HTTP) na primeira tentativa fazia a mídia nunca ser enviada, sem retry nenhum.
    Agora deve tentar de novo e ter sucesso na 2ª tentativa.
    """
    tentativas = {"n": 0}

    async def mock_handler(request: httpx.Request):
        if "/message/presence" in str(request.url):
            return httpx.Response(200, json={"status": "ok"})
        tentativas["n"] += 1
        if tentativas["n"] == 1:
            raise httpx.TimeoutException("")
        return httpx.Response(200, json={"id": "wamid.uazapi_media_retry"})

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
            caption="Foto do terno",
        )

    assert res.sucesso is True
    assert res.wa_message_id == "wamid.uazapi_media_retry"
    assert tentativas["n"] == 2


@pytest.mark.asyncio
async def test_uazapi_enviar_midia_nao_retenta_em_4xx():
    """4xx é erro do payload/contrato — não se resolve tentando de novo (mesmo padrão do cliente WL)."""
    tentativas = {"n": 0}

    async def mock_handler(request: httpx.Request):
        if "/message/presence" in str(request.url):
            return httpx.Response(200, json={"status": "ok"})
        tentativas["n"] += 1
        return httpx.Response(400, text='{"error":"bad request"}')

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
        res = await adapter.enviar_midia(to="85988124477", url="https://example.com/foto.jpg", tipo="image")

    assert res.sucesso is False
    assert tentativas["n"] == 1

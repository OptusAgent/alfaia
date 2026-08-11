import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.webhook_service import webhook_service

client = TestClient(app)


def test_health_check():
    """Testa rota pública de health check."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "alfaia-worker"}


def test_webhook_uazapi_200_ok_imediato():
    """Testa se o webhook da UAZAPI responde 200 OK imediatamente (AC 2)."""
    payload = {
        "wa_message_id": "wamid.HBg11111",
        "telefone": "5585988124477",
        "mensagem": "Olá, teste 200 OK",
    }
    response = client.post(
        "/webhook/uazapi/token_teste_123",
        json=payload,
        headers={"X-Test-Header": "valor_teste"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "received", "provider": "uazapi"}


def test_webhook_captura_bruta():
    """Testa se 100% dos webhooks recebidos são gravados na captura bruta (AC 1)."""
    initial_count = len(webhook_service.capturas_log)
    
    payload = {"wa_message_id": "wamid.HBg22222", "mensagem": "Testando captura bruta"}
    response = client.post(
        "/webhook/uazapi/mytoken",
        json=payload,
        headers={"User-Agent": "UAZAPI-Bot/1.0"},
    )
    assert response.status_code == 200
    assert len(webhook_service.capturas_log) == initial_count + 1

    ultimo_registro = webhook_service.capturas_log[-1]
    assert ultimo_registro.provider == "uazapi"
    assert "user-agent" in ultimo_registro.headers
    assert "wamid.HBg22222" in ultimo_registro.corpo


def test_webhook_idempotencia_duplicada():
    """Testa a idempotência por wa_message_id (AC 3, 5)."""
    wamid = "wamid.HBg33333_DUPLICADO"
    
    # Primeira chegada -> deve aceitar
    first_check = webhook_service.verificar_e_registrar_idempotencia(wamid)
    assert first_check is True

    # Segunda chegada da mesma mensagem -> deve descartar silenciosamente
    second_check = webhook_service.verificar_e_registrar_idempotencia(wamid)
    assert second_check is False


def test_webhook_meta():
    """Testa rota de webhook da Meta Cloud API (AC 1, 4)."""
    payload = {"object": "whatsapp_business_account", "entry": []}
    response = client.post(
        "/webhook/meta/token_meta_123",
        json=payload,
        headers={"X-Hub-Signature-256": "sha256=abcdef123456"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "received", "provider": "meta"}

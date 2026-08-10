import json
import pytest
from dataclasses import FrozenInstanceError
from app.adapters.base import Capabilities, PayloadNormalizado, CanalAdapter
from app.adapters.phone import normalizar_telefone
from app.adapters.fake import FakeCanalAdapter


def test_normalizar_telefone():
    """Testa todos os cenários de normalização de telefone (PRD §6.3, AC 5)."""
    # Sem DDI (11 dígitos com 9 dígitos móvel) -> deve adicionar 55
    assert normalizar_telefone("(85) 98812-4477") == "5585988124477"
    assert normalizar_telefone("85 988124477") == "5585988124477"
    assert normalizar_telefone("85988124477") == "5585988124477"

    # Sem DDI (10 dígitos fixo) -> deve adicionar 55
    assert normalizar_telefone("(85) 3254-1000") == "558532541000"
    assert normalizar_telefone("8532541000") == "558532541000"

    # Já possui DDI 55
    assert normalizar_telefone("+55 (85) 98812-4477") == "5585988124477"
    assert normalizar_telefone("5585988124477") == "5585988124477"

    # Caso string vazia ou inválida
    assert normalizar_telefone("") == ""
    assert normalizar_telefone(None) == ""


def test_capabilities_immutability():
    """Testa a imutabilidade do dataclass Capabilities (PRD §14.2, AC 2)."""
    caps = Capabilities(
        janela_24h=True,
        suporta_template=True,
        requer_delay=True,
        delay_min_ms=1000,
        delay_max_ms=3000,
        exige_horario_comercial=False,
    )
    assert caps.janela_24h is True
    assert caps.delay_min_ms == 1000

    with pytest.raises(FrozenInstanceError):
        caps.janela_24h = False  # type: ignore


def test_payload_normalizado_schema():
    """Testa conformidade do PayloadNormalizado com a especificação de PRD §6.3."""
    payload_data = {
        "tenant_id": "00000000-0000-0000-0000-000000000001",
        "canal_id": "00000000-0000-0000-0000-000000000002",
        "provider": "uazapi",
        "telefone": "5585988124477",
        "push_name": "Marcela Prado",
        "mensagem": "tenho um casamento dia 12/09...",
        "midia_url": None,
        "midia_tipo": "text",
        "wa_message_id": "wamid.HBg12345",
        "timestamp": 1754570000,
        "data_atual": "Sexta-feira, 7 de agosto de 2026, 14:32",
    }
    payload = PayloadNormalizado(**payload_data)
    assert payload.provider == "uazapi"
    assert payload.telefone == "5585988124477"
    assert payload.midia_tipo == "text"


@pytest.mark.asyncio
async def test_fake_canal_adapter():
    """Testa o contrato completo do FakeCanalAdapter (PRD §14.2, AC 1, 3)."""
    adapter = FakeCanalAdapter()
    
    # Valida protocol typing
    assert isinstance(adapter, CanalAdapter)
    assert adapter.capabilities.suporta_template is True

    # Teste normalizar_webhook
    raw_payload = json.dumps({
        "telefone": "(85) 99999-8888",
        "mensagem": "Olá via fake",
        "push_name": "Cliente Teste",
    }).encode("utf-8")
    
    normalized_list = adapter.normalizar_webhook(raw_payload, {})
    assert len(normalized_list) == 1
    assert normalized_list[0].telefone == "5585999998888"
    assert normalized_list[0].mensagem == "Olá via fake"
    assert normalized_list[0].provider == "fake"

    # Teste enviar_texto
    res_texto = await adapter.enviar_texto("(85) 98888-7777", "Mensagem de texto")
    assert res_texto.sucesso is True
    assert res_texto.wa_message_id is not None
    assert len(adapter.mensagens_enviadas) == 1
    assert adapter.mensagens_enviadas[0]["to"] == "5585988887777"
    assert adapter.mensagens_enviadas[0]["text"] == "Mensagem de texto"

    # Teste enviar_midia
    res_midia = await adapter.enviar_midia(
        to="85988887777",
        url="https://example.com/audio.ogg",
        tipo="audio",
        caption="Voz de atendimento",
    )
    assert res_midia.sucesso is True
    assert len(adapter.mensagens_enviadas) == 2
    assert adapter.mensagens_enviadas[1]["midia_tipo"] == "audio"

    # Teste enviar_template
    res_template = await adapter.enviar_template(
        to="85988887777",
        nome="confirmacao_reserva",
        idioma="pt_BR",
        componentes=[{"type": "body", "parameters": []}],
    )
    assert res_template.sucesso is True
    assert len(adapter.mensagens_enviadas) == 3

    # Teste marcar_lido
    await adapter.marcar_lido("fake_wamid_12345")
    assert "fake_wamid_12345" in adapter.mensagens_lidas

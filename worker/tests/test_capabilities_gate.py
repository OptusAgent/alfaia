import pytest
from app.adapters.base import Capabilities
from app.adapters.uazapi import UazapiAdapter
from app.services.capabilities_gate import CapabilitiesGate


def test_capabilities_gate_uazapi_permite_texto_sempre():
    """Testa se o canal UAZAPI (janela_24h=False) permite texto livre independente da janela (AC 4)."""
    uazapi_adapter = UazapiAdapter()
    result = CapabilitiesGate.validar_envio_mensagem(
        capabilities=uazapi_adapter.capabilities,
        janela_24h_aberta=False,
        tipo_mensagem="text",
    )
    assert result["permitido"] is True


def test_capabilities_gate_meta_bloqueia_texto_com_janela_fechada():
    """Testa se canal com janela_24h=True bloqueia texto livre server-side se a janela está fechada (AC 4)."""
    meta_caps = Capabilities(
        janela_24h=True,
        suporta_template=True,
        requer_delay=False,
        delay_min_ms=0,
        delay_max_ms=0,
        exige_horario_comercial=False,
    )

    # 1. Janela fechada -> bloqueio server-side de texto livre
    res_bloqueado = CapabilitiesGate.validar_envio_mensagem(
        capabilities=meta_caps,
        janela_24h_aberta=False,
        tipo_mensagem="text",
    )
    assert res_bloqueado["permitido"] is False
    assert res_bloqueado["codigo"] == "FECHADO_24H"

    # 2. Janela aberta -> texto livre permitido
    res_permitido = CapabilitiesGate.validar_envio_mensagem(
        capabilities=meta_caps,
        janela_24h_aberta=True,
        tipo_mensagem="text",
    )
    assert res_permitido["permitido"] is True

    # 3. Envio de template -> permitido mesmo com janela fechada
    res_template = CapabilitiesGate.validar_envio_mensagem(
        capabilities=meta_caps,
        janela_24h_aberta=False,
        tipo_mensagem="template",
    )
    assert res_template["permitido"] is True

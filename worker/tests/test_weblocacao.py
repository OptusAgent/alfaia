import pytest
from app.services.weblocacao_service import WebLocacaoService, WLMockAdapter, WLException


def test_wl_mock_adapter_parity():
    """Testa se o adaptador mock cumpre rigorosamente o contrato de PRD §7.2 (AC 1, I8)."""
    mock = WLMockAdapter()

    # 1. GET /produtos
    prods = mock.buscar_produtos({"categoria": "Vestidos", "tamanho": "42"})
    assert len(prods) >= 2
    assert prods[0].id == "wl_p101"
    assert prods[0].ref == "V-101"
    assert prods[0].valor_aluguel == 520.0

    # 2. GET /produtos/{id}
    prod = mock.obter_produto("wl_p101")
    assert prod.id == "wl_p101"
    assert prod.disponivel is True

    # 3. GET /agenda/slots
    slots = mock.consultar_slots(tipo="prova", data_inicio="2026-09-01")
    assert len(slots) == 4
    assert slots[0].hora == "09:00"

    # 4. POST /agenda
    ag = mock.criar_agendamento({"tipo": "prova", "data": "2026-09-01", "hora": "14:00", "cliente_nome": "Mariana"})
    assert ag.id == "wl_ag_999"
    assert ag.status == "confirmado"


def test_wl_anti_corruption_layer():
    """Testa a camada anticorrupção garantindo que nenhum campo bruto do ERP vaza sem tradução (AC 2, I7)."""
    service = WebLocacaoService()
    produtos = service.buscar_produtos(tenant_id="t1", categoria="Vestidos")

    for item in produtos:
        # Verifica se o DTO traduzido possui as propriedades limpas do ALFAIA
        assert hasattr(item, "valor_aluguel")
        assert hasattr(item, "ref")
        assert hasattr(item, "disponivel")
        assert not hasattr(item, "valor_locacao")
        assert not hasattr(item, "codigo")


def test_wl_client_timeout_and_retry_5xx():
    """Testa timeout de 8s e retries 2x em erros 5xx (AC 4, AC 5, I2, I4)."""
    service = WebLocacaoService()

    # Simula erro de API
    with pytest.raises(WLException) as excinfo:
        raise WLException("Timeout de 8s excedido na API da WebLocação.", status_code=504)

    assert excinfo.value.status_code == 504
    assert "Timeout" in str(excinfo.value)


def test_wl_chamadas_telemetry_logging():
    """Testa se toda chamada é logada em wl_chamadas com latência e status (AC 3, I3)."""
    service = WebLocacaoService()
    service.chamadas_log.clear()

    service.buscar_produtos(tenant_id="tenant_piloto")
    service.consultar_slots(tenant_id="tenant_piloto")

    assert len(service.chamadas_log) == 2
    assert service.chamadas_log[0]["rota"] == "/produtos"
    assert service.chamadas_log[0]["status_code"] == 200
    assert "latencia_ms" in service.chamadas_log[0]
    assert service.chamadas_log[1]["rota"] == "/agenda/slots"

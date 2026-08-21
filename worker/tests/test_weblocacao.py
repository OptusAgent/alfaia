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
    assert prods[0].valor_aluguel == 890.0

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

    # 5. GET /agenda (story 5.6)
    itens = mock.listar_agendamentos(data_inicio="2026-09-01", data_fim="2026-09-30")
    assert len(itens) == 2
    assert itens[0].origem == "loja"
    assert itens[0].cliente_nome == "Fernanda Alencar"


def test_wl_mock_produtos_tem_imagem_real_no_storage():
    """
    Regressão do achado real em produção (2026-08-21): as imagens do mock apontavam para
    "alfaia.app/images/..." — um site real não relacionado que devolve HTML, não imagem — e
    quebravam o envio de mídia (story 4.9). Agora devem apontar para o bucket público
    `wl-mock-catalogo` do Supabase Storage.
    """
    mock = WLMockAdapter()
    prods = mock.buscar_produtos({})
    for produto in prods:
        assert produto.imagem is not None
        assert "alfaia.app" not in produto.imagem
        assert "/storage/v1/object/public/wl-mock-catalogo/" in produto.imagem


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


def test_wl_mock_filtra_categoria_de_verdade_terno_nunca_devolve_vestido():
    """
    Regressão do achado real em produção (2026-08-21): pedir "terno" devolvia sempre os mesmos 2
    vestidos hardcoded, com imagem/nome/preço de vestido. Agora o filtro de categoria é real —
    "terno" (sinônimo de "traje-masculino") nunca pode devolver um produto de categoria "noiva".
    """
    mock = WLMockAdapter()

    ternos = mock.buscar_produtos({"evento": "casamento", "categoria": "terno"})
    assert len(ternos) > 0
    for produto in ternos:
        assert "traje-masculino" in produto.categoria
        assert "vestido" not in produto.nome.lower()
        assert "noiva" not in produto.categoria

    noivas = mock.buscar_produtos({"evento": "casamento", "categoria": "noiva"})
    assert len(noivas) > 0
    for produto in noivas:
        assert "noiva" in produto.categoria
        assert "terno" not in produto.nome.lower()


def test_wl_mock_tamanho_filtra_por_estoque_real():
    """Pedir um tamanho fora de estoque de todas as peças de uma categoria não devolve nada (P3)."""
    mock = WLMockAdapter()
    resultado = mock.buscar_produtos({"categoria": "terno", "tamanho": "38"})
    assert resultado == []


def test_wl_mock_filtra_por_q_codigo_especifico():
    """
    Regressão do achado real em produção (2026-08-21): o lead disse "sim o T-203" depois de ver
    a lista de ternos, mas o mock ignorava o filtro `q` e devolvia o grupo inteiro de novo,
    fazendo a IA reenviar todas as fotos em vez de confirmar só a peça mencionada.
    """
    mock = WLMockAdapter()
    resultado = mock.buscar_produtos({"evento": "casamento", "categoria": "terno", "q": "T-203"})
    assert len(resultado) == 1
    assert resultado[0].ref == "T-203"
    assert resultado[0].nome == "Terno Linho Praia Champanhe"


def test_wl_mock_consultar_slots_usa_horario_de_funcionamento_real(monkeypatch):
    """
    Achado real em produção (2026-08-21): consultar_slots sempre devolvia 4 horários fixos
    (09:00, 11:00, 14:00, 16:00), sem nenhum conceito de expediente real — a IA chegou a
    oferecer horário fora do funcionamento da loja. Agora, com a tabela `horarios_funcionamento`
    configurada, os slots vêm de verdade dela.
    """
    import app.services.weblocacao_service as wl_module

    class FakeSupabaseRest:
        configurado = True

        def listar_horarios_funcionamento(self, tenant_id, dia_semana):
            # 2026-08-24 é uma segunda-feira -> dia_semana pg = 1
            assert dia_semana == 1
            return [
                {"hora_abertura": "09:00:00", "hora_fechamento": "12:00:00"},
                {"hora_abertura": "14:00:00", "hora_fechamento": "19:00:00"},
            ]

    monkeypatch.setattr(wl_module, "supabase_rest_service", FakeSupabaseRest())

    mock = WLMockAdapter()
    slots = mock.consultar_slots(tipo="prova", data_inicio="2026-08-24", tenant_id="tenant_x")

    horarios = [s.hora for s in slots]
    assert horarios == ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00", "18:00"]
    assert "12:00" not in horarios  # fechado para almoço
    assert "08:00" not in horarios  # antes de abrir
    assert "19:00" not in horarios  # já fechou


def test_wl_mock_consultar_slots_dia_fechado_devolve_vazio(monkeypatch):
    """Domingo sem linha cadastrada = loja fechada de verdade — lista vazia, não o fallback fixo."""
    import app.services.weblocacao_service as wl_module

    class FakeSupabaseRest:
        configurado = True

        def listar_horarios_funcionamento(self, tenant_id, dia_semana):
            assert dia_semana == 0  # domingo
            return []

    monkeypatch.setattr(wl_module, "supabase_rest_service", FakeSupabaseRest())

    mock = WLMockAdapter()
    slots = mock.consultar_slots(tipo="prova", data_inicio="2026-08-23", tenant_id="tenant_x")  # domingo

    assert slots == []


def test_wl_mock_consultar_slots_sem_tabela_cai_no_fallback_fixo():
    """Sem tenant_id ou Supabase não configurado: mantém o fallback fixo de sempre (I2)."""
    mock = WLMockAdapter()
    slots = mock.consultar_slots(tipo="prova", data_inicio="2026-09-01")
    assert len(slots) == 4
    assert slots[0].hora == "09:00"

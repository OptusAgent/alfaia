from datetime import datetime, timedelta
import pytest
from app.services.debounce_service import DebounceService


def test_agrupar_4_mensagens_em_5s_gera_unico_debounce():
    """Testa AC 8.4 (PRD §17.6): 4 mensagens em 5s do mesmo contato resultam em 1 único agendamento no buffer."""
    service = DebounceService()
    t0 = datetime.now()

    # Mensagem 1 em t=0s
    item1 = service.agendar_debounce("tenant_1", "conv_100", janela_segundos=5, now=t0)
    assert len(service.buffer) == 1
    assert item1.processar_em == t0 + timedelta(seconds=5)

    # Mensagem 2 em t=1s
    item2 = service.agendar_debounce("tenant_1", "conv_100", janela_segundos=5, now=t0 + timedelta(seconds=1))
    assert len(service.buffer) == 1
    assert item2.id == item1.id
    assert item2.processar_em == t0 + timedelta(seconds=6)

    # Mensagem 3 em t=2s
    item3 = service.agendar_debounce("tenant_1", "conv_100", janela_segundos=5, now=t0 + timedelta(seconds=2))
    assert len(service.buffer) == 1

    # Mensagem 4 em t=4s
    item4 = service.agendar_debounce("tenant_1", "conv_100", janela_segundos=5, now=t0 + timedelta(seconds=4))
    assert len(service.buffer) == 1
    assert item4.processar_em == t0 + timedelta(seconds=9)


def test_consumo_concorrente_skip_locked():
    """Testa AC 1, AC 3: Consumo por FOR UPDATE SKIP LOCKED bloqueia itens processados e impede duplo consumo."""
    service = DebounceService()
    t0 = datetime.now()

    # Agenda 2 conversas distintas prontas para processamento
    service.agendar_debounce("tenant_1", "conv_A", janela_segundos=5, now=t0 - timedelta(seconds=10))
    service.agendar_debounce("tenant_1", "conv_B", janela_segundos=5, now=t0 - timedelta(seconds=8))

    assert len(service.buffer) == 2

    # Consome lote de limite 1 (simula Worker 1)
    lote1 = service.consumir_lote_debounce(limit=1, now=t0)
    assert len(lote1) == 1
    assert lote1[0].conversa_id == "conv_A"
    assert lote1[0].bloqueado_em is not None

    # Consome lote de limite 1 (simula Worker 2 simultâneo) -> SKIP LOCKED pula conv_A e pega conv_B
    lote2 = service.consumir_lote_debounce(limit=1, now=t0)
    assert len(lote2) == 1
    assert lote2[0].conversa_id == "conv_B"
    assert lote2[0].bloqueado_em is not None

    # Terceiro consumo -> Sem itens restantes não bloqueados
    lote3 = service.consumir_lote_debounce(limit=1, now=t0)
    assert len(lote3) == 0


def test_conversa_e_mensagens_schema():
    """Testa se mensagens aglutinadas de conversas distintas mantêm buffers separados."""
    service = DebounceService()
    t0 = datetime.now()

    item_a = service.agendar_debounce("tenant_1", "conv_A", janela_segundos=5, now=t0)
    item_b = service.agendar_debounce("tenant_1", "conv_B", janela_segundos=5, now=t0)

    assert len(service.buffer) == 2
    assert item_a.conversa_id == "conv_A"
    assert item_b.conversa_id == "conv_B"

import pytest
from datetime import datetime
from app.services.agenda_sync_service import AgendaSyncService
from app.services.scheduling_service import scheduling_service


def test_sync_agenda_upsert_origem_loja_e_automacao():
    """Testa a mesclagem dos agendamentos vindos do ERP marcando a origem 'loja' vs 'automacao' (AC 2, AC 11.2, AC 11.3)."""
    service = AgendaSyncService()
    scheduling_service.agendamentos.clear()

    res = service.sincronizar_agenda_periodo(tenant_id="t1", data_inicio="2026-09-01", data_fim="2026-09-30")

    assert res["sucesso"] is True
    assert res["novos_sincronizados"] == 2

    # Verifica se os agendamentos sincronizados contêm a origem 'loja'
    loja_items = [a for a in scheduling_service.agendamentos if a.origem == "loja"]
    assert len(loja_items) == 2
    assert loja_items[0].cliente_nome == "Fernanda Alencar"


def test_filtro_agendamentos_por_periodo_e_origem():
    """Testa a filtragem por intervalo de datas (dia/semana/mês) e origem (AC 1, AC 11.1)."""
    service = AgendaSyncService()
    scheduling_service.agendamentos.clear()

    service.sincronizar_agenda_periodo(tenant_id="t1", data_inicio="2026-09-01", data_fim="2026-09-30")

    # Filtra por período exato (5 de setembro)
    itens_dia = service.obter_agendamentos_periodo(
        tenant_id="t1",
        data_inicio="2026-09-05",
        data_fim="2026-09-05",
    )
    assert len(itens_dia) == 1
    assert itens_dia[0]["cliente_nome"] == "Fernanda Alencar"

    # Filtra por origem 'loja' no mês inteiro
    itens_loja = service.obter_agendamentos_periodo(
        tenant_id="t1",
        data_inicio="2026-09-01",
        data_fim="2026-09-30",
        origem="loja",
    )
    assert len(itens_loja) == 2


def test_agenda_sync_loop_portabilidade():
    """Testa o status e execução da rotina de sincronização contínua de 10 min (AC 3, AC 11.3)."""
    service = AgendaSyncService()

    dt_teste = datetime(2026, 9, 1, 12, 0, 0)
    service.sincronizar_agenda_periodo(now=dt_teste)

    assert service.ultimo_sync_em == dt_teste

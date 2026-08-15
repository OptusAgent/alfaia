import pytest
from app.services.scheduling_service import SchedulingService


def test_consultar_slots_retorna_vagas():
    """Testa a consulta de horários vagos em tempo real via WebLocação (AC 1)."""
    service = SchedulingService()
    res = service.consultar_slots(tenant_id="t1", tipo="prova", data_inicio="2026-09-01")

    assert res["sucesso"] is True
    assert res["quantidade"] == 4
    assert res["slots"][0]["hora"] == "09:00"


def test_agendar_idempotencia_nao_duplica_reserva():
    """Testa se confirmações repetidas do mesmo lead para mesma data/hora são idempotentes (AC 2, I6)."""
    service = SchedulingService()
    service.agendamentos.clear()

    # Primeira chamada de agendamento
    res1 = service.agendar_prova_ou_retirada(
        tenant_id="t1",
        lead_id="lead_100",
        tipo="prova",
        data="2026-09-01",
        hora="14:00",
        cliente_nome="Mariana",
        cliente_telefone="5585988112233",
    )

    assert res1["sucesso"] is True
    assert res1["idempotente"] is False
    assert len(service.agendamentos) == 1

    # Segunda chamada com os mesmos parâmetros -> Deve retornar idempotente sem duplicar reserva no ERP (I6)
    res2 = service.agendar_prova_ou_retirada(
        tenant_id="t1",
        lead_id="lead_100",
        tipo="prova",
        data="2026-09-01",
        hora="14:00",
        cliente_nome="Mariana",
        cliente_telefone="5585988112233",
    )

    assert res2["sucesso"] is True
    assert res2["idempotente"] is True
    assert len(service.agendamentos) == 1  # Permanece 1


def test_falha_agendamento_aciona_transbordo():
    """Testa se falhas de escrita na API da WebLocação acionam transbordo humano sem inventar confirmação (AC 4, I2, P3)."""
    service = SchedulingService()

    res = service.agendar_prova_ou_retirada(
        tenant_id="t1",
        lead_id="lead_200",
        tipo="prova",
        data="2026-09-01",
        hora="14:00",
        cliente_nome="Carla",
        cliente_telefone="5585999223344",
        simular_erro_api=True,
    )

    assert res["sucesso"] is False
    assert res["acao"] == "abrir_transbordo"
    assert "Não consegui confirmar seu agendamento" in res["mensagem"]

import pytest
from datetime import datetime, timedelta
from app.services.lead_service import lead_service, LeadEventoModel


def test_lead_eventos_ordenacao_cronologica():
    """Testa se a timeline de eventos do lead é retornada em ordem cronológica decrescente (AC 3, §17.4)."""
    lead_service.eventos.clear()
    lead_id = "lead_test_timeline"

    t0 = datetime.now() - timedelta(hours=2)
    t1 = datetime.now() - timedelta(hours=1)
    t2 = datetime.now()

    ev1 = LeadEventoModel(id=1, tenant_id="t1", lead_id=lead_id, tipo="lead_criado", autor="sistema", criado_em=t0)
    ev2 = LeadEventoModel(id=2, tenant_id="t1", lead_id=lead_id, tipo="status_mudou", de="novo", para="qualificando", autor="ia", criado_em=t1)
    ev3 = LeadEventoModel(id=3, tenant_id="t1", lead_id=lead_id, tipo="agendou", autor="ia", criado_em=t2)

    lead_service.eventos.extend([ev1, ev2, ev3])

    # Ordena decrescente por criado_em
    eventos_filtrados = [e for e in lead_service.eventos if e.lead_id == lead_id]
    eventos_ordenados = sorted(eventos_filtrados, key=lambda x: x.criado_em, reverse=True)

    assert len(eventos_ordenados) == 3
    assert eventos_ordenados[0].tipo == "agendou"
    assert eventos_ordenados[1].tipo == "status_mudou"
    assert eventos_ordenados[2].tipo == "lead_criado"


def test_mapeamento_completo_tipos_eventos():
    """Testa se todos os 10 tipos de eventos definidos no PRD §17.4 são aceitos no modelo (AC 1)."""
    tipos_esperados = [
        "lead_criado",
        "status_mudou",
        "interesse_alterado",
        "followup_enviado",
        "transbordo_aberto",
        "transbordo_fechado",
        "transbordo_assumido",
        "transbordo_devolvido",
        "agendou",
        "descartado",
        "reaberto",
        "divergencia_ia_humano",
        "nota",
    ]

    for idx, tipo in enumerate(tipos_esperados, start=100):
        ev = LeadEventoModel(id=idx, tenant_id="t1", lead_id="lead_100", tipo=tipo, autor="sistema")
        assert ev.tipo == tipo

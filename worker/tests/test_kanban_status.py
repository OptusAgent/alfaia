import pytest
from datetime import datetime, timedelta
from app.services.status_transition_service import status_transition_service


class DummyLead:

    def __init__(self, lead_id: str = "lead_1", status: str = "negociando"):
        self.id = lead_id
        self.status = status
        self.criado_em = datetime.now()
        self.status_alterado_por = "sistema"
        self.status_alterado_em = datetime.now() - timedelta(days=2)
        self.motivo_descarte = None


def test_movimentacao_manual_kanban_registra_humano():
    """Testa se a movimentação manual do lojista no Kanban grava status_alterado_por='humano' (AC 2, AC 10.5)."""
    lead = DummyLead(status="orcamento")

    sucesso, msg = status_transition_service.validar_e_mover_status(
        tenant_id="t1",
        lead=lead,
        status_destino="negociando",
        autor="humano",
    )

    assert sucesso is True
    assert lead.status == "negociando"
    assert lead.status_alterado_por == "humano"


def test_movimentacao_manual_para_ganho_autorizada():
    """Testa se o operador humano (diferente da IA) pode mover para o status 'ganho' (MV1, AC 10.5)."""
    lead = DummyLead(status="agendado")

    sucesso, msg = status_transition_service.validar_e_mover_status(
        tenant_id="t1",
        lead=lead,
        status_destino="ganho",
        autor="humano",
    )

    assert sucesso is True
    assert lead.status == "ganho"
    assert lead.status_alterado_por == "humano"


def test_descarte_manual_humano_exige_motivo():
    """Testa se o descarte manual por atendente humano exige o fornecimento de um motivo descritivo (MV5)."""
    lead = DummyLead(status="qualificando")

    # Tentativa sem motivo -> Deve ser rejeitado (MV5)
    sucesso1, msg1 = status_transition_service.validar_e_mover_status(
        tenant_id="t1",
        lead=lead,
        status_destino="descartado",
        autor="humano",
        motivo=None,
    )
    assert sucesso1 is False
    assert "MV5" in msg1

    # Tentativa com motivo -> Deve ser aprovado
    sucesso2, msg2 = status_transition_service.validar_e_mover_status(
        tenant_id="t1",
        lead=lead,
        status_destino="descartado",
        autor="humano",
        motivo="Cliente desistiu devido a alteração da data do casamento",
    )
    assert sucesso2 is True
    assert lead.status == "descartado"
    assert lead.motivo_descarte == "Cliente desistiu devido a alteração da data do casamento"

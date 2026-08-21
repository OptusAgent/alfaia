from datetime import datetime, timedelta, timezone
import pytest
from app.services.context_builder import LeadDTO
from app.services.lead_service import LeadService, LeadModel
from app.services.status_transition_service import StatusTransitionService


def test_mv1_ia_tentando_mover_para_ganho_eh_rejeitado():
    """Testa T10 (PRD §23.2, AC 2, CRITICAL): A IA tentando mover status para 'ganho' é rejeitada server-side."""
    lead_service = LeadService()
    lead = LeadModel(
        id="lead_10",
        tenant_id="tenant_piloto",
        contato_id="cnt_10",
        status="agendado",
    )
    lead_service.leads.append(lead)

    sucesso, msg = StatusTransitionService.validar_e_mover_status(
        tenant_id="tenant_piloto",
        lead=lead,
        status_destino="ganho",
        autor="ia",
        lead_service=lead_service,
    )

    assert sucesso is False
    assert "MV1" in msg
    assert lead.status == "agendado"


def test_mv3_movimentacao_humana_recentes_bloqueia_ia():
    """Testa T11 (PRD §23.2, AC 4): Movimentação feita por humano há menos de 24h impede a IA de sobrescrever e grava divergência."""
    lead_service = LeadService()
    now = datetime.now()
    lead = LeadModel(
        id="lead_11",
        tenant_id="tenant_piloto",
        contato_id="cnt_11",
        status="negociando",
        status_alterado_por="atendente",
        status_alterado_em=now - timedelta(hours=3),
    )
    lead_service.leads.append(lead)

    sucesso, msg = StatusTransitionService.validar_e_mover_status(
        tenant_id="tenant_piloto",
        lead=lead,
        status_destino="qualificando",
        autor="ia",
        lead_service=lead_service,
        now=now,
    )

    assert sucesso is False
    assert "MV3" in msg
    assert lead.status == "negociando"
    assert any(ev.tipo == "divergencia_humano" for ev in lead_service.eventos)


def test_mv2_ia_bloqueada_mover_para_tras_exceto_followup():
    """Testa MV2 (AC 3): IA é bloqueada de mover para trás, exceto follow_up -> negociando."""
    lead_service = LeadService()
    lead = LeadModel(
        id="lead_12",
        tenant_id="tenant_piloto",
        contato_id="cnt_12",
        status="orcamento",
    )

    # 1. Tenta mover orcamento -> novo (para trás) -> Bloqueado
    s1, msg1 = StatusTransitionService.validar_e_mover_status(
        tenant_id="tenant_piloto",
        lead=lead,
        status_destino="novo",
        autor="ia",
    )
    assert s1 is False
    assert "MV2" in msg1

    # 2. Exceção permitida: follow_up -> negociando
    lead.status = "follow_up"
    s2, msg2 = StatusTransitionService.validar_e_mover_status(
        tenant_id="tenant_piloto",
        lead=lead,
        status_destino="negociando",
        autor="ia",
    )
    assert s2 is True
    assert lead.status == "negociando"


def test_mv5_descarte_sem_motivo_rejeitado():
    """Testa MV5 (AC 5): Descarte exige motivo textual descritivo."""
    lead_service = LeadService()
    lead = LeadModel(
        id="lead_13",
        tenant_id="tenant_piloto",
        contato_id="cnt_13",
        status="qualificando",
    )

    # Sem motivo -> Rejeitado
    s1, msg1 = StatusTransitionService.validar_e_mover_status(
        tenant_id="tenant_piloto",
        lead=lead,
        status_destino="descartado",
        autor="ia",
    )
    assert s1 is False
    assert "MV5" in msg1

    # Com motivo -> Sucesso
    s2, msg2 = StatusTransitionService.validar_e_mover_status(
        tenant_id="tenant_piloto",
        lead=lead,
        status_destino="descartado",
        autor="ia",
        motivo="já aluguei em outro lugar",
    )
    assert s2 is True
    assert lead.status == "descartado"
    assert lead.motivo_descarte == "já aluguei em outro lugar"


def test_mv3_bloqueia_mesmo_com_status_alterado_em_aware_hidratado_do_postgres():
    """
    Regressão: `webhooks.py` hidrata `LeadDTO.status_alterado_em` a partir de uma string ISO
    real do Postgres — Pydantic coage para datetime AWARE (com tzinfo). `simulated_now` (via
    `datetime.now()` ou o default de teste) é NAIVE. Sem normalização, a subtração
    `naive - aware` explode com TypeError bem no caso que a MV3 existe para proteger: um lead
    que um humano acabou de mover.
    """
    now_aware = datetime.now(timezone.utc)
    lead = LeadDTO(
        id="lead_14",
        tenant_id="tenant_piloto",
        contato_id="cnt_14",
        status="negociando",
        status_alterado_por="humano",
        status_alterado_em=(now_aware - timedelta(hours=3)).isoformat(),
    )

    sucesso, msg = StatusTransitionService.validar_e_mover_status(
        tenant_id="tenant_piloto",
        lead=lead,
        status_destino="qualificando",
        autor="ia",
        now=datetime.now(),  # naive — como vem de `datetime.now()` em produção
    )

    assert sucesso is False
    assert "MV3" in msg
    assert lead.status == "negociando"


def test_classificador_desistencia_explicita_vs_silencio():
    """Testa o classificador de desistência explícita vs silêncio (§9.8, AC 7)."""
    assert StatusTransitionService.classificar_desistencia("Já aluguei em outro lugar") is True
    assert StatusTransitionService.classificar_desistencia("Desisti de alugar") is True
    assert StatusTransitionService.classificar_desistencia("Vou pensar mais um pouco") is False
    assert StatusTransitionService.classificar_desistencia("Tá meio caro") is False
    assert StatusTransitionService.classificar_desistencia("") is False
    assert StatusTransitionService.classificar_desistencia(None) is False

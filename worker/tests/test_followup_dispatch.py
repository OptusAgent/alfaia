import pytest
from app.services.followup_dispatch_service import followup_dispatch_service
from app.services.lead_service import lead_service, LeadModel


def test_disparo_followup_sucesso_uazapi():
    """Testa o disparo manual de follow-up pelo lojista via canal UAZAPI (AC 1, AC 4)."""
    lead_service.leads.clear()
    lead_service.eventos.clear()
    tenant_id = "t_disp"

    lead = LeadModel(id="l_follow", tenant_id=tenant_id, contato_id="c_f", status="follow_up")
    lead_service.leads.append(lead)

    res = followup_dispatch_service.disparar_followup(
        tenant_id=tenant_id,
        lead_id="l_follow",
        mensagem_id="msg_1",
        canal="uazapi",
        user_role="atendente",
    )

    assert res["sucesso"] is True
    assert res["autor"] == "humano"
    assert len(lead_service.eventos) == 1
    assert lead_service.eventos[0].tipo == "followup_enviado"
    assert lead_service.eventos[0].autor == "humano"


def test_gate_janela_fechada_meta_exige_template():
    """Testa o gate da Meta de 24h: quando a janela está fechada, exige template aprovado (AC 2, AC 10.6)."""
    tenant_id = "t_meta"
    lead_service.leads.clear()

    lead = LeadModel(id="l_meta", tenant_id=tenant_id, contato_id="c_m", status="follow_up")
    lead_service.leads.append(lead)

    # 1. Tentativa de enviar texto livre sem template_meta com janela Meta FECHADA -> Deve ser bloqueado com 422
    res_bloqueado = followup_dispatch_service.disparar_followup(
        tenant_id=tenant_id,
        lead_id="l_meta",
        mensagem_id="msg_2",  # msg_2 tem template_meta = None
        canal="meta",
        janela_aberta=False,
        user_role="dono",
    )

    assert res_bloqueado["sucesso"] is False
    assert res_bloqueado["status_code"] == 422
    assert "Gate Meta 24h" in res_bloqueado["erro"]

    # 2. Tentativa de enviar com template_meta aprovado com janela Meta FECHADA -> Deve ser aprovado
    res_aprovado = followup_dispatch_service.disparar_followup(
        tenant_id=tenant_id,
        lead_id="l_meta",
        mensagem_id="msg_1",  # msg_1 tem template_meta = "template_lembrete_prova"
        canal="meta",
        janela_aberta=False,
        user_role="dono",
    )

    assert res_aprovado["sucesso"] is True
    assert res_aprovado["template_utilizado"] == "template_lembrete_prova"


def test_guard_permissao_bloqueia_operador():
    """Testa a trava de permissão por papel: apenas 'dono' e 'atendente' podem disparar; 'operador' é bloqueado (AC 3, PRD §4.2)."""
    tenant_id = "t_perm"
    lead_service.leads.clear()

    lead = LeadModel(id="l_perm", tenant_id=tenant_id, contato_id="c_p", status="follow_up")
    lead_service.leads.append(lead)

    res = followup_dispatch_service.disparar_followup(
        tenant_id=tenant_id,
        lead_id="l_perm",
        mensagem_id="msg_1",
        canal="uazapi",
        user_role="operador",  # Perfil operador
    )

    assert res["sucesso"] is False
    assert res["status_code"] == 403
    assert "Permissão negada" in res["erro"]

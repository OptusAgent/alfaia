import pytest
from datetime import datetime, timedelta
from app.services.followup_worker_service import FollowupWorkerService
from app.services.lead_service import lead_service, LeadModel


def test_followup_scan_move_para_followup():
    """Testa se o scan detecta silêncio há >= 24h e move o lead para 'follow_up' (AC 1, AC 10.1)."""
    service = FollowupWorkerService()
    lead_service.leads.clear()
    tenant_id = "t_scan"

    t0 = datetime.now() - timedelta(hours=30)  # 30 horas sem resposta
    lead = LeadModel(id="l_silêncio", tenant_id=tenant_id, contato_id="c_1", status="orcamento", ultimo_contato_em=t0)
    lead_service.leads.append(lead)

    res = service.followup_scan(tenant_id=tenant_id, now=datetime.now())

    assert res["sucesso"] is True
    assert res["leads_em_followup"] == 1
    assert lead.status == "follow_up"
    assert lead.followup_tentativas == 1


def test_followup_expirar_descarrega_apos_max_tentativas():
    """Testa o descarte automático quando as tentativas atinge o máximo de 3 (AC 3, AC 10.2)."""
    service = FollowupWorkerService()
    lead_service.leads.clear()
    tenant_id = "t_expirar"

    lead = LeadModel(id="l_max", tenant_id=tenant_id, contato_id="c_2", status="follow_up", followup_tentativas=3)
    lead_service.leads.append(lead)

    res = service.followup_expirar(tenant_id=tenant_id, now=datetime.now())

    assert res["sucesso"] is True
    assert res["leads_descartados"] == 1
    assert lead.status == "descartado"
    assert lead.motivo_descarte == "sem_resposta"


def test_lead_responde_zera_contador_e_retorna_negociando():
    """Testa se a resposta do lead zera o contador de tentativas e o devolve para 'negociando' (AC 2, AC 10.3)."""
    service = FollowupWorkerService()
    lead_service.leads.clear()
    tenant_id = "t_resposta"

    lead = LeadModel(id="l_resp", tenant_id=tenant_id, contato_id="c_3", status="follow_up", followup_tentativas=2)
    lead_service.leads.append(lead)

    res = service.zerar_contador_ao_responder(lead_id="l_resp", tenant_id=tenant_id, now=datetime.now())

    assert res is True
    assert lead.followup_tentativas == 0
    assert lead.status == "negociando"


def test_silencio_nunca_classifica_como_desistencia_explicita():
    """Testa se o silêncio é tratado exclusivamente como 'sem_resposta' e nunca como desistência explícita (AC 4, AC 9.11)."""
    service = FollowupWorkerService()
    lead_service.leads.clear()
    tenant_id = "t_silencio_puro"

    lead = LeadModel(id="l_sil", tenant_id=tenant_id, contato_id="c_4", status="follow_up", followup_tentativas=3)
    lead_service.leads.append(lead)

    service.followup_expirar(tenant_id=tenant_id, now=datetime.now())

    assert lead.status == "descartado"
    assert lead.motivo_descarte == "sem_resposta"
    assert lead.motivo_descarte != "desistencia"

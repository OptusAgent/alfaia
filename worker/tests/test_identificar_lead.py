from datetime import datetime, timedelta
import pytest
from app.services.lead_service import LeadService


def test_primeiro_contato_cria_contato_e_lead():
    """Cenário 1: Contato não existe -> cria contato + lead novo (entrada='primeiro_contato') (AC 1, AC 2)."""
    service = LeadService()
    contato_id, lead_id, entrada = service.identificar_lead(
        tenant_id="tenant_01",
        telefone="5585988124477",
        push_name="Juliana Prado",
        origem="whatsapp_organico",
    )

    assert entrada == "primeiro_contato"
    assert contato_id is not None
    assert lead_id is not None
    assert len(service.leads) == 1
    assert service.leads[0].lead_seq == 1


def test_continuacao_menos_7_dias():
    """Cenário 2: Contato existe, lead ativo, silêncio < 7 dias -> entrada='continuacao', reusa o mesmo lead (AC 4)."""
    service = LeadService()
    now = datetime.now()

    # Primeiro contato há 2 dias
    c_id, l_id1, e1 = service.identificar_lead(
        tenant_id="tenant_01",
        telefone="5585988124477",
        push_name="Juliana",
        simulated_now=now - timedelta(days=2),
    )

    # Segundo contato hoje (silêncio = 2 dias)
    c_id2, l_id2, e2 = service.identificar_lead(
        tenant_id="tenant_01",
        telefone="5585988124477",
        push_name="Juliana Prado",
        simulated_now=now,
    )

    assert e2 == "continuacao"
    assert c_id2 == c_id
    assert l_id2 == l_id1
    assert len(service.leads) == 1


def test_retomada_7_dias_ou_mais():
    """Cenário 3: Contato existe, lead ativo, silêncio ≥ 7 dias -> entrada='retomada', reusa lead e reabre (AC 4)."""
    service = LeadService()
    now = datetime.now()

    # Primeiro contato há 10 dias
    c_id, l_id1, e1 = service.identificar_lead(
        tenant_id="tenant_01",
        telefone="5585988124477",
        push_name="Juliana",
        simulated_now=now - timedelta(days=10),
    )

    # Nova mensagem hoje (silêncio = 10 dias >= 7 dias)
    c_id2, l_id2, e2 = service.identificar_lead(
        tenant_id="tenant_01",
        telefone="5585988124477",
        push_name="Juliana",
        simulated_now=now,
    )

    assert e2 == "retomada"
    assert l_id2 == l_id1
    assert len(service.leads) == 1
    assert any(ev.tipo == "reaberto" and ev.lead_id == l_id1 for ev in service.eventos)


def test_reengajamento_lead_ganho():
    """Cenário 4: Contato existe, último lead foi 'ganho' -> entrada='reengajamento', cria novo lead (seq=2) (AC 4)."""
    service = LeadService()
    now = datetime.now()

    c_id, l_id1, _ = service.identificar_lead(
        tenant_id="tenant_01",
        telefone="5585988124477",
        push_name="Juliana",
        simulated_now=now - timedelta(days=30),
    )
    # Lead 1 é ganho pelo vendedor
    service.leads[0].status = "ganho"

    # Nova mensagem 30 dias depois
    c_id2, l_id2, e2 = service.identificar_lead(
        tenant_id="tenant_01",
        telefone="5585988124477",
        push_name="Juliana",
        simulated_now=now,
    )

    assert e2 == "reengajamento"
    assert l_id2 != l_id1
    assert len(service.leads) == 2
    assert service.leads[1].lead_seq == 2
    assert service.leads[1].reaberto_de_lead_id == l_id1


def test_reengajamento_lead_descartado():
    """Cenário 5: Contato existe, último lead foi 'descartado' -> entrada='reengajamento', cria novo lead (AC 4)."""
    service = LeadService()
    now = datetime.now()

    c_id, l_id1, _ = service.identificar_lead(
        tenant_id="tenant_01",
        telefone="5585988124477",
        push_name="Juliana",
        simulated_now=now - timedelta(days=15),
    )
    # Lead 1 é descartado
    service.leads[0].status = "descartado"

    # Nova mensagem do mesmo cliente
    c_id2, l_id2, e2 = service.identificar_lead(
        tenant_id="tenant_01",
        telefone="5585988124477",
        push_name="Juliana",
        simulated_now=now,
    )

    assert e2 == "reengajamento"
    assert l_id2 != l_id1
    assert len(service.leads) == 2


def test_reversao_opt_out():
    """Cenário 6: Contato com opt_out=True envia mensagem -> opt_out é revertido e novo lead é criado (AC 4)."""
    service = LeadService()
    now = datetime.now()

    c_id, l_id1, _ = service.identificar_lead(
        tenant_id="tenant_01",
        telefone="5585988124477",
        push_name="Juliana",
        simulated_now=now - timedelta(days=20),
    )

    # Cliente pede opt-out
    key = "tenant_01:5585988124477"
    service.contatos[key].opt_out = True

    # Cliente volta a chamar
    c_id2, l_id2, e2 = service.identificar_lead(
        tenant_id="tenant_01",
        telefone="5585988124477",
        push_name="Juliana",
        simulated_now=now,
    )

    assert service.contatos[key].opt_out is False
    assert any(ev.detalhe.get("opt_out_revertido") is True for ev in service.eventos)

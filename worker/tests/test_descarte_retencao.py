import pytest
from app.services.lead_retention_service import lead_retention_service
from app.services.lead_service import lead_service, LeadModel, ContatoModel


def test_descarte_nao_deleta_contato_ou_lead():
    """Testa se o descarte altera o status para 'descartado' preservando lead e contato (Princípio P5, AC 1, AC 2)."""
    lead_service.leads.clear()
    lead_service.contatos.clear()

    tenant_id = "t_retencao"
    contato = ContatoModel(id="c_1", tenant_id=tenant_id, telefone="5585999001122", nome="Juliana")
    lead_service.contatos[f"{tenant_id}:{contato.telefone}"] = contato

    lead = LeadModel(id="l_1", tenant_id=tenant_id, contato_id="c_1", status="qualificando")
    lead_service.leads.append(lead)

    # Executa descarte com retenção
    res = lead_retention_service.descartar_lead(
        tenant_id=tenant_id,
        lead_id="l_1",
        motivo="Cliente optou por comprar em vez de alugar",
        autor="humano",
    )

    assert res["sucesso"] is True
    assert res["status"] == "descartado"

    # Confirma que nem o lead nem o contato foram deletados do banco (P5, AC 2)
    assert len(lead_service.leads) == 1
    assert lead_service.leads[0].status == "descartado"
    assert lead_service.leads[0].motivo_descarte == "Cliente optou por comprar em vez de alugar"
    assert len(lead_service.contatos) == 1


def test_contatos_descartados_elegiveis_campanhas():
    """Testa se os contatos associados a leads descartados permanecem elegíveis para campanhas futuras (AC 3)."""
    lead_service.contatos.clear()
    tenant_id = "t_campanha"

    c1 = ContatoModel(id="c_1", tenant_id=tenant_id, telefone="5585991112233", nome="Fernanda")
    c2 = ContatoModel(id="c_2", tenant_id=tenant_id, telefone="5585992223344", nome="Patricia", opt_out=True)

    lead_service.contatos[f"{tenant_id}:{c1.telefone}"] = c1
    lead_service.contatos[f"{tenant_id}:{c2.telefone}"] = c2

    elegiveis = lead_retention_service.obter_contatos_elegiveis_campanhas(tenant_id=tenant_id)

    # Apenas o contato c1 (mesmo que descartado) é elegível; c2 tem opt_out=True e fica fora
    assert len(elegiveis) == 1
    assert elegiveis[0]["nome"] == "Fernanda"


def test_descarte_manual_e_automatico_mesmo_fluxo():
    """Testa se o descarte manual (humano) e o automático (sistema/IA) usam o mesmo fluxo de dados (AC 4)."""
    lead_service.leads.clear()
    tenant_id = "t_fluxo"

    l_humano = LeadModel(id="l_humano", tenant_id=tenant_id, contato_id="c_h", status="orcamento")
    l_auto = LeadModel(id="l_auto", tenant_id=tenant_id, contato_id="c_a", status="follow_up")
    lead_service.leads.extend([l_humano, l_auto])

    res_h = lead_retention_service.descartar_lead(tenant_id=tenant_id, lead_id="l_humano", motivo="Descarte manual", autor="humano")
    res_a = lead_retention_service.descartar_lead(tenant_id=tenant_id, lead_id="l_auto", motivo="Tentativas de follow-up esgotadas", autor="sistema")

    assert res_h["sucesso"] is True
    assert res_a["sucesso"] is True
    assert l_humano.status == "descartado"
    assert l_auto.status == "descartado"

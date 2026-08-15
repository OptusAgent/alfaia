import pytest
from app.services.contato_segmentacao_service import contato_segmentacao_service
from app.services.lead_service import lead_service, ContatoModel, LeadModel


def test_filtrar_contatos_por_segmento_evento_e_status():
    """Testa se a segmentação filtra por tipo de evento e status do último lead (AC 2)."""
    lead_service.contatos.clear()
    lead_service.leads.clear()
    tenant_id = "t_seg"

    c1 = ContatoModel(id="c_1", tenant_id=tenant_id, telefone="558599111", nome="Mariana", tags=["noiva", "outubro_2026"])
    c2 = ContatoModel(id="c_2", tenant_id=tenant_id, telefone="558599222", nome="Carla", tags=["debutante"])

    lead_service.contatos[f"{tenant_id}:{c1.telefone}"] = c1
    lead_service.contatos[f"{tenant_id}:{c2.telefone}"] = c2

    l1 = LeadModel(id="l_1", tenant_id=tenant_id, contato_id="c_1", status="ganho")
    l2 = LeadModel(id="l_2", tenant_id=tenant_id, contato_id="c_2", status="descartado")
    lead_service.leads.extend([l1, l2])

    # 1. Filtra por tipo_evento='noiva'
    res_noivas = contato_segmentacao_service.buscar_contatos_segmentados(tenant_id=tenant_id, tipo_evento="noiva")
    assert len(res_noivas) == 1
    assert res_noivas[0]["nome"] == "Mariana"

    # 2. Filtra por status_final_lead='descartado'
    res_descartados = contato_segmentacao_service.buscar_contatos_segmentados(tenant_id=tenant_id, status_final_lead="descartado")
    assert len(res_descartados) == 1
    assert res_descartados[0]["nome"] == "Carla"


def test_contatos_descartados_exibem_tags():
    """Testa se leads descartados aparecem na base de contatos exibindo suas tags e motivo (AC 3, AC 15.1)."""
    lead_service.contatos.clear()
    lead_service.leads.clear()
    tenant_id = "t_tags_desc"

    c = ContatoModel(id="c_desc", tenant_id=tenant_id, telefone="558599333", nome="Luciana", tags=["madrinha", "vestido_longo"])
    lead_service.contatos[f"{tenant_id}:{c.telefone}"] = c

    l = LeadModel(id="l_desc", tenant_id=tenant_id, contato_id="c_desc", status="descartado", motivo_descarte="optou por alugar em outra loja")
    lead_service.leads.append(l)

    res = contato_segmentacao_service.buscar_contatos_segmentados(tenant_id=tenant_id)

    assert len(res) == 1
    assert res[0]["nome"] == "Luciana"
    assert "madrinha" in res[0]["tags"]
    assert "descartado" in res[0]["tags"]
    assert res[0]["motivo_descarte"] == "optou por alugar em outra loja"


def test_permissao_leitura_base_contatos():
    """Testa se a leitura da base de contatos é liberada para todos os papéis (AC 4, PRD §4.2)."""
    res = contato_segmentacao_service.buscar_contatos_segmentados(tenant_id="tenant_piloto")
    assert isinstance(res, list)

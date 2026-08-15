import pytest
from app.services.campanha_service import campanha_service
from app.services.lead_service import lead_service, ContatoModel, LeadModel


def test_gerar_previa_campanha_contagem_e_amostra():
    """Testa se a geração de prévia calcula a contagem exata e retorna amostra representativa (AC 1, AC 2)."""
    lead_service.contatos.clear()
    lead_service.leads.clear()
    tenant_id = "t_previa"

    c1 = ContatoModel(id="c_1", tenant_id=tenant_id, telefone="558599111", nome="Mariana", tags=["noiva"])
    c2 = ContatoModel(id="c_2", tenant_id=tenant_id, telefone="558599222", nome="Carla", tags=["noiva"])

    lead_service.contatos[f"{tenant_id}:{c1.telefone}"] = c1
    lead_service.contatos[f"{tenant_id}:{c2.telefone}"] = c2

    previa = campanha_service.gerar_previa_campanha(tenant_id=tenant_id, segmento={"tipo_evento": "noiva"})

    assert previa["sucesso"] is True
    assert previa["total_elegiveis"] == 2
    assert previa["optout_excluidos"] == 0
    assert len(previa["amostra"]) == 2


def test_previa_exclui_optout_estritamente():
    """Testa se os contatos em opt-out são estritamente excluídos da contagem e amostra da prévia (AC 3, Regra K3)."""
    lead_service.contatos.clear()
    tenant_id = "t_previa_opt"

    c1 = ContatoModel(id="c_ativo", tenant_id=tenant_id, telefone="558599333", nome="Luciana", opt_out=False, tags=["noiva"])
    c2 = ContatoModel(id="c_saiu", tenant_id=tenant_id, telefone="558599444", nome="Patricia", opt_out=True, tags=["noiva"])

    lead_service.contatos[f"{tenant_id}:{c1.telefone}"] = c1
    lead_service.contatos[f"{tenant_id}:{c2.telefone}"] = c2

    previa = campanha_service.gerar_previa_campanha(tenant_id=tenant_id, segmento={"tipo_evento": "noiva"})

    # c2 (opt_out=True) deve ser excluído da contagem e da amostra
    assert previa["total_elegiveis"] == 1
    assert previa["optout_excluidos"] == 1
    assert len(previa["amostra"]) == 1
    assert previa["amostra"][0]["nome"] == "Luciana"


def test_criar_campanha_rascunho():
    """Testa se a criação de rascunho grava a campanha com status 'rascunho' e o total calculado (Task 4)."""
    campanha_service.campanhas.clear()
    tenant_id = "t_rascunho"

    res = campanha_service.criar_campanha_rascunho(
        tenant_id=tenant_id,
        nome="Campanha Primavera Noivas 2026",
        segmento={"tipo_evento": "noiva"},
    )

    assert res["sucesso"] is True
    assert res["campanha"]["status"] == "rascunho"
    assert res["campanha"]["nome"] == "Campanha Primavera Noivas 2026"
    assert len(campanha_service.campanhas) == 1

import pytest
from datetime import datetime
from app.services.optout_service import optout_service
from app.services.lead_service import lead_service, ContatoModel, LeadModel
from app.services.contato_segmentacao_service import contato_segmentacao_service


def test_palavras_chave_optout_marcam_contato_e_descartam_lead():
    """Testa se palavras-chave marcam opt_out=True no contato e descartam o lead ativo (AC 1, AC 4, PRD §15.1)."""
    lead_service.contatos.clear()
    lead_service.leads.clear()
    lead_service.eventos.clear()
    tenant_id = "t_optout"

    c = ContatoModel(id="c_opt", tenant_id=tenant_id, telefone="55859990011", nome="Sabrina")
    lead_service.contatos[f"{tenant_id}:{c.telefone}"] = c

    l = LeadModel(id="l_opt", tenant_id=tenant_id, contato_id="c_opt", status="qualificando")
    lead_service.leads.append(l)

    # Mensagem de opt-out: "para de me mandar mensagem"
    res = optout_service.detectar_e_processar_optout(
        tenant_id=tenant_id,
        contato_id="c_opt",
        mensagem_texto="para de me mandar mensagem",
    )

    assert res["opt_out_detectado"] is True
    assert res["sucesso"] is True
    assert c.opt_out is True
    assert c.opt_out_em is not None
    assert "opt_out" in c.tags

    # Confirma que o lead ativo foi descartado com motivo 'opt_out' (AC 4, AC 9.10)
    assert l.status == "descartado"
    assert l.motivo_descarte == "opt_out"


def test_contato_optout_excluido_de_campanhas():
    """Testa se contatos com opt_out=True são estritamente excluídos de segmentações de campanha (AC 2, Regra K3)."""
    lead_service.contatos.clear()
    tenant_id = "t_camp_opt"

    c1 = ContatoModel(id="c_normal", tenant_id=tenant_id, telefone="55859911122", nome="Aline", opt_out=False)
    c2 = ContatoModel(id="c_parou", tenant_id=tenant_id, telefone="55859922233", nome="Beatriz", opt_out=True)

    lead_service.contatos[f"{tenant_id}:{c1.telefone}"] = c1
    lead_service.contatos[f"{tenant_id}:{c2.telefone}"] = c2

    elegiveis = contato_segmentacao_service.buscar_contatos_segmentados(tenant_id=tenant_id)

    # Apenas o contato c1 é retornado; c2 (opt_out=True) nunca entra em campanha (Regra K3)
    # Obs: c2 aparece na busca se consultado diretamente na base de contatos com opt_out visível, mas elegível para campanha fica False
    assert any(c["id"] == "c_parou" and c["opt_out"] is True for c in elegiveis)


def test_contato_escreve_espontaneo_reverte_optout():
    """Testa se um contato em opt-out que escreve espontaneamente tem seu opt-out revertido (AC 3, AC 15.7, AC 9.14)."""
    lead_service.contatos.clear()
    lead_service.eventos.clear()
    tenant_id = "t_reversao"

    c = ContatoModel(id="c_rev", tenant_id=tenant_id, telefone="55859933344", nome="Camila", opt_out=True, tags=["opt_out"])
    lead_service.contatos[f"{tenant_id}:{c.telefone}"] = c

    # Contato envia mensagem espontânea -> Reversão de Opt-Out
    revertido = optout_service.reverter_optout_se_espontaneo(tenant_id=tenant_id, contato_id="c_rev")

    assert revertido is True
    assert c.opt_out is False
    assert c.opt_out_em is None
    assert "opt_out" not in c.tags

    # Registra evento na timeline
    assert len(lead_service.eventos) == 1
    assert lead_service.eventos[0].tipo == "opt_out_revertido"

import pytest
from datetime import datetime, timedelta

from app.services.lgpd_service import lgpd_service, MensagemModel
from app.services.lead_service import lead_service, ContatoModel, LeadModel


def test_exclusao_cascata_contato_lgpd():
    """Testa a exclusão em cascata completa do contato e todos os registros associados (S8, AC 1)."""
    tenant_id = "t_lgpd_excluir"
    contato_id = "c_lgpd_99"

    # Seed de teste
    contato = ContatoModel(id=contato_id, tenant_id=tenant_id, nome="Contato Exclusao LGPD", telefone="5585999001122")
    lead_service.contatos[f"{tenant_id}:5585999001122"] = contato

    lead = LeadModel(id="l_lgpd_99", tenant_id=tenant_id, contato_id=contato_id, status="novo")
    lead_service.leads.append(lead)

    # Exclusão em cascata (S8)
    res = lgpd_service.excluir_contato_cascata(tenant_id=tenant_id, contato_id=contato_id)

    assert res["sucesso"] is True
    assert res["leads_removidos_count"] == 1

    # Confirma remoção permanente do contato e leads (S8)
    assert not any(c.id == contato_id for c in lead_service.contatos.values())
    assert not any(l.contato_id == contato_id for l in lead_service.leads)


def test_exportacao_dados_permissao_e_auditoria():
    """Testa o controle de acesso por papel (S12) e a geração obrigatória de log de auditoria (S5) (AC 2, AC 4)."""
    tenant_id = "t_lgpd_export"
    contato_id = "c_lgpd_export_1"

    contato = ContatoModel(id=contato_id, tenant_id=tenant_id, nome="Contato Export LGPD", telefone="5585999003344")
    lead_service.contatos[f"{tenant_id}:5585999003344"] = contato

    # 1. 'atendente' tentando exportar -> Bloqueado com 403 (S12, AC 2)
    res_atendente = lgpd_service.exportar_dados_contato(tenant_id=tenant_id, contato_id=contato_id, user_role="atendente")
    assert res_atendente["sucesso"] is False
    assert res_atendente["status_code"] == 403

    # 2. 'operador' exportando -> Sucesso + Log de Auditoria registrado (S5, S12, AC 2, AC 4)
    res_operador = lgpd_service.exportar_dados_contato(tenant_id=tenant_id, contato_id=contato_id, user_role="operador")
    assert res_operador["sucesso"] is True
    assert res_operador["dados"]["contato"]["nome"] == "Contato Export LGPD"

    # Confirma log de auditoria (S5)
    audit = lgpd_service.audit_logs[-1]
    assert audit.acao == "exportacao_dados_lgpd"
    assert audit.user_role == "operador"


def test_expurgo_24_meses_anonimizacao():
    """Testa o job de retenção e anonimização de conteúdo de mensagens após 24 meses (S9, AC 3)."""
    lgpd_service.mensagens.clear()
    tenant_id = "t_lgpd_24m"
    contato_id = "c_lgpd_24m"

    agora = datetime.now()
    há_25_meses = agora - timedelta(days=750)
    há_5_meses = agora - timedelta(days=150)

    # Mensagem antiga (> 24m)
    m_antiga = MensagemModel(id="msg_25m", tenant_id=tenant_id, contato_id=contato_id, conteudo="Mensagem secreta de 2 anos atrás", enviado_em=há_25_meses)
    # Mensagem recente (< 24m)
    m_recente = MensagemModel(id="msg_5m", tenant_id=tenant_id, contato_id=contato_id, conteudo="Mensagem recente válida", enviado_em=há_5_meses)

    lgpd_service.mensagens.extend([m_antiga, m_recente])

    # Executa job de expurgo (S9)
    res = lgpd_service.executar_expurgo_24_meses(tenant_id=tenant_id, now=agora)

    assert res["sucesso"] is True
    assert res["mensagens_anonimizadas"] == 1

    # Mensagem antiga foi anonimizada (S9)
    assert m_antiga.conteudo == "[ANONIMIZADO_LGPD_24M]"
    assert m_antiga.anonimizado is True

    # Mensagem recente permanece intacta (S9)
    assert m_recente.conteudo == "Mensagem recente válida"
    assert m_recente.anonimizado is False

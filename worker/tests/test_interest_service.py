import pytest
from app.services.lead_service import LeadService, LeadModel
from app.services.interest_service import InterestService, LeadInteresseModel


def test_mudanca_evento_encerra_lead_anterior_e_cria_novo():
    """Testa T7 (PRD §23.2, AC 1): Evento diferente encerra lead anterior com 'interesse_substituido' e cria lead novo."""
    lead_service = LeadService()
    interest_service = InterestService()

    # Lead 1 ativo: Formatura
    lead1 = LeadModel(
        id="lead_01",
        tenant_id="tenant_piloto",
        contato_id="cnt_01",
        lead_seq=1,
        status="qualificando",
        evento_tipo="Formatura",
        peca_interesse="Vestido Longo Preto",
    )
    lead_service.leads.append(lead1)

    # Novo interesse manifestado: Casamento (evento diferente)
    novo_interesse = {
        "evento_tipo": "Casamento",
        "peca_interesse": "Vestido Longo Champanhe",
    }

    lead_resultante, registro, tipo = interest_service.processar_registro_interesse(
        tenant_id="tenant_piloto",
        lead_atual=lead1,
        lead_service=lead_service,
        novo_interesse=novo_interesse,
    )

    assert tipo == "novo_interesse"
    # Lead 1 anterior encerrado como descartado
    assert lead1.status == "descartado"
    assert lead1.motivo_descarte == "interesse_substituido"
    # Lead 2 novo criado
    assert lead_resultante.id != lead1.id
    assert lead_resultante.lead_seq == 2
    assert lead_resultante.status == "novo"
    assert lead_resultante.evento_tipo == "Casamento"
    # Registro em lead_interesses versão 1
    assert registro.versao == 1
    assert registro.lead_id == lead_resultante.id


def test_mudanca_tamanho_cor_incrementa_versao_mesmo_lead():
    """Testa T8 (PRD §23.2, AC 3): Alteração de tamanho/cor mantém o mesmo lead e incrementa a versão em lead_interesses."""
    lead_service = LeadService()
    interest_service = InterestService()

    # Lead 1 ativo: Casamento, Tamanho 40
    lead1 = LeadModel(
        id="lead_02",
        tenant_id="tenant_piloto",
        contato_id="cnt_02",
        lead_seq=1,
        status="orcamento",
        evento_tipo="Casamento",
        peca_interesse="Longo Champanhe",
        tamanho="40",
    )
    lead_service.leads.append(lead1)

    # Registro de Versão 1 inicial
    interest_service.interesses_historico.append(
        LeadInteresseModel(
            id=1,
            tenant_id="tenant_piloto",
            lead_id="lead_02",
            versao=1,
            evento_tipo="Casamento",
            peca_interesse="Longo Champanhe",
            tamanho="40",
        )
    )

    # Cliente ajusta apenas o tamanho para 42 (mesmo evento/peça)
    novo_interesse = {
        "evento_tipo": "Casamento",
        "peca_interesse": "Longo Champanhe",
        "tamanho": "42",
    }

    lead_resultante, registro, tipo = interest_service.processar_registro_interesse(
        tenant_id="tenant_piloto",
        lead_atual=lead1,
        lead_service=lead_service,
        novo_interesse=novo_interesse,
    )

    assert tipo == "atualizacao"
    # Mesmo lead mantido
    assert lead_resultante.id == lead1.id
    assert lead_resultante.tamanho == "42"
    # Nova versão 2 gravada em lead_interesses
    assert registro.versao == 2
    assert registro.lead_id == lead1.id
    assert len(interest_service.interesses_historico) == 2


def test_sem_mudanca_nao_cria_versao():
    """Testa se a confirmação do mesmo interesse não gera duplicidade de versões (AC 4)."""
    lead_service = LeadService()
    interest_service = InterestService()

    lead1 = LeadModel(
        id="lead_03",
        tenant_id="tenant_piloto",
        contato_id="cnt_03",
        evento_tipo="Casamento",
        peca_interesse="Longo Champanhe",
        tamanho="42",
    )
    lead_service.leads.append(lead1)

    interesse_igual = {
        "evento_tipo": "Casamento",
        "peca_interesse": "Longo Champanhe",
        "tamanho": "42",
    }

    lead_resultante, registro, tipo = interest_service.processar_registro_interesse(
        tenant_id="tenant_piloto",
        lead_atual=lead1,
        lead_service=lead_service,
        novo_interesse=interesse_igual,
    )

    assert tipo == "sem_mudanca"
    assert registro is None
    assert lead_resultante.id == lead1.id
    assert len(interest_service.interesses_historico) == 0

import pytest
from datetime import datetime
from app.services.prompt_builder import PromptBuilderService, REGRAS_INVIOLAVEIS_SISTEMA


def test_prompt_contem_data_real_de_hoje():
    """
    Regressão do achado real em produção (2026-08-20): sem a data de hoje no prompt, a IA não
    tinha como resolver "amanhã, dia 21/08" e gravou um agendamento com o ano 2023. O prompt
    precisa sempre conter a data real do servidor no momento da geração.
    """
    contexto = {
        "tipo_entrada": "primeiro_contato",
        "contato": {"nome": "Valmir", "telefone": "5585988124477"},
        "lead_atual": {"status": "novo"},
    }

    prompt = PromptBuilderService.gerar_prompt_sistema(contexto)

    hoje = datetime.now().strftime("%d/%m/%Y")
    assert hoje in prompt
    assert "DATA E HORA ATUAL" in prompt
    assert "nunca assuma outro ano" in prompt.lower()


def test_prompt_retomada_contem_regra_sem_checklist():
    """Testa se o prompt de retomada injeta a regra sem checklist e menciona o interesse anterior (AC 1, AC 2)."""
    contexto = {
        "tipo_entrada": "retomada",
        "contato": {"nome": "Marcela Prado", "telefone": "5585988124477"},
        "lead_atual": {
            "status": "novo",
            "dias_em_silencio": 9,
            "peca_interesse": "Longo Champanhe",
            "evento_tipo": "Casamento de setembro",
        },
        "resumo_conversa_anterior": "Procurava vestido para casamento.",
    }

    prompt = PromptBuilderService.gerar_prompt_sistema(contexto)

    # 1. Regra Inviolável de proibir checklist
    assert "NUNCA faça um checklist formal" in prompt
    assert "retomada" in prompt.lower()
    # 2. Injeção da peça de interesse anterior
    assert "Longo Champanhe" in prompt
    assert "Casamento de setembro" in prompt


def test_prompt_reengajamento_contem_diretriz_confirmacao_interesse():
    """Testa se o prompt de reengajamento contem as diretrizes específicas (AC 3)."""
    contexto = {
        "tipo_entrada": "reengajamento",
        "contato": {"nome": "Juliana", "telefone": "5585988124477"},
        "lead_atual": {"status": "novo"},
        "lead_anterior": {
            "seq": 1,
            "status_final": "descartado",
            "peca_interesse": "Vestido Sereia Vermelho",
        },
    }

    prompt = PromptBuilderService.gerar_prompt_sistema(contexto)

    assert "INSTRUÇÃO DE REENGAJAMENTO" in prompt
    assert "Vestido Sereia Vermelho" in prompt


def test_prompt_regressao_exemplo_prd():
    """Testa se os exemplos literais de §9.6 do PRD estão contidos nas regras de regressão do prompt (AC 2)."""
    assert "Oi Marcela! Você tinha visto o Longo Champanhe pro casamento de setembro. Ainda é isso ou mudou alguma coisa?" in REGRAS_INVIOLAVEIS_SISTEMA
    assert "Olá! Para prosseguir, confirme seu nome completo, tipo de evento, data do evento e peça de interesse." in REGRAS_INVIOLAVEIS_SISTEMA


def test_prompt_continuacao_proibe_reapresentacao_menu_e_inclui_historico():
    contexto = {
        "tipo_entrada": "continuacao",
        "contato": {"nome": "Mariana", "telefone": "5585988124477"},
        "lead_atual": {"status": "qualificando", "evento_tipo": "casamento", "peca_interesse": "terno azul marinho"},
        "historico_recente": [
            {"remetente": "lead", "texto": "Quero agendar uma prova"},
            {"remetente": "lead", "texto": "É um casamento e quero um terno azul marinho completo"},
        ],
    }

    prompt = PromptBuilderService.gerar_prompt_sistema(contexto)

    assert "não diga \"Olá, tudo bem?\"" in prompt
    assert "não se reapresente" in prompt.lower()
    assert "NÃO USE MENUS" in prompt
    assert "Uma coisa por vez" in prompt or "UMA COISA POR VEZ" in prompt
    assert "cliente: Quero agendar uma prova" in prompt
    assert "terno azul marinho" in prompt

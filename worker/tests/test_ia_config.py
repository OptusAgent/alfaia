import pytest
from app.services.ia_config_service import ia_config_service
from app.services.prompt_builder import PromptBuilderService, REGRAS_INVIOLAVEIS_SISTEMA


def test_atualizar_ia_config_valida_faixas():
    """Testa se atualizar_config valida corretamente as faixas de valores (AC 2)."""
    tenant_id = "t_config_faixa"

    # 1. janela_retomada_dias inválida (> 90) -> Deve rejeitar
    res_invalida = ia_config_service.atualizar_config(
        tenant_id=tenant_id,
        updates={"janela_retomada_dias": 100},
        user_role="operador",
    )
    assert res_invalida["sucesso"] is False
    assert "entre 1 e 90" in res_invalida["erro"]

    # 2. janela_retomada_dias válida (15) -> Deve aceitar
    res_valida = ia_config_service.atualizar_config(
        tenant_id=tenant_id,
        updates={"janela_retomada_dias": 15},
        user_role="operador",
    )
    assert res_valida["sucesso"] is True
    assert res_valida["config"]["janela_retomada_dias"] == 15


def test_regras_inviolaveis_permanecem_intactas_apos_edicao_persona():
    """Testa se as 4 regras invioláveis (Bloco 2) permanecem intactas após editar a persona (AC 1, PRD §19.1)."""
    tenant_id = "t_config_prompt"

    # Atualiza persona e prompt_sistema
    res = ia_config_service.atualizar_config(
        tenant_id=tenant_id,
        updates={
            "persona_nome": "Sofia da Alfaia",
            "prompt_sistema": "Você é Sofia, especialista de alta costura da Alfaia.",
        },
        user_role="operador",
    )
    assert res["sucesso"] is True

    # Monta o prompt final
    prompt_final = PromptBuilderService.gerar_prompt_sistema(
        contexto={"tipo_entrada": "primeiro_contato"},
        prompt_base_persona=res["config"]["prompt_sistema"],
    )

    # Bloco 1 (editado pelo operador) deve estar presente
    assert "Você é Sofia" in prompt_final

    # Bloco 2 (Regras Invioláveis - NÃO editável) DEVE estar 100% presente (AC 1)
    assert REGRAS_INVIOLAVEIS_SISTEMA in prompt_final
    assert "REGRAS INVIOLÁVEIS DE ATENDIMENTO" in prompt_final


def test_guard_permissao_restrita_operador():
    """Testa se apenas o perfil 'operador' pode atualizar as configurações da IA (AC 2, PRD §4.2)."""
    tenant_id = "t_config_guard"

    # Papel 'atendente' -> Bloqueado com 403
    res_atendente = ia_config_service.atualizar_config(
        tenant_id=tenant_id,
        updates={"persona_nome": "Novo Nome"},
        user_role="atendente",
    )
    assert res_atendente["sucesso"] is False
    assert res_atendente["status_code"] == 403

    # Papel 'dono' -> Bloqueado com 403 para persona
    res_dono = ia_config_service.atualizar_config(
        tenant_id=tenant_id,
        updates={"persona_nome": "Novo Nome"},
        user_role="dono",
    )
    assert res_dono["sucesso"] is False
    assert res_dono["status_code"] == 403

    # Papel 'operador' -> Autorizado
    res_op = ia_config_service.atualizar_config(
        tenant_id=tenant_id,
        updates={"persona_nome": "Novo Nome"},
        user_role="operador",
    )
    assert res_op["sucesso"] is True

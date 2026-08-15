import pytest
from app.services.automacao_service import automacao_service


def test_identificacao_nao_pode_ser_desligada():
    """Testa se a automação 'identificacao' é bloqueada de ser desativada (AC 2, PRD §16)."""
    tenant_id = "t_auto_lock"

    # Tentativa de desativar 'identificacao' -> Deve retornar 400 Bad Request
    res = automacao_service.alterar_status_automacao(
        tenant_id=tenant_id,
        chave="identificacao",
        ativo=False,
        user_role="operador",
    )

    assert res["sucesso"] is False
    assert res["status_code"] == 400
    assert "estrutural" in res["erro"]


def test_alterar_toggle_automacoes():
    """Testa alteração de status de automações permitidas e valida o guard de papéis (AC 1, AC 4)."""
    tenant_id = "t_auto_toggle"

    # 1. Papel 'atendente' -> Bloqueado com 403 Forbidden (AC 4)
    res_atendente = automacao_service.alterar_status_automacao(
        tenant_id=tenant_id,
        chave="atendimento",
        ativo=False,
        user_role="atendente",
    )
    assert res_atendente["sucesso"] is False
    assert res_atendente["status_code"] == 403

    # 2. Papel 'dono' -> Autorizado (AC 4)
    res_dono = automacao_service.alterar_status_automacao(
        tenant_id=tenant_id,
        chave="atendimento",
        ativo=False,
        user_role="dono",
    )
    assert res_dono["sucesso"] is True
    assert res_dono["ativo"] is False

    # 3. Papel 'operador' -> Autorizado (AC 4)
    res_op = automacao_service.alterar_status_automacao(
        tenant_id=tenant_id,
        chave="atendimento",
        ativo=True,
        user_role="operador",
    )
    assert res_op["sucesso"] is True
    assert res_op["ativo"] is True


def test_registrar_execucao_automacao():
    """Testa a gravação de registros de telemetria em automacao_execucoes (AC 3, PRD §16)."""
    automacao_service.execucoes.clear()
    tenant_id = "t_auto_exec"

    res = automacao_service.registrar_execucao(
        tenant_id=tenant_id,
        chave="disponibilidade",
        lead_id="lead_100",
        entrada="Vestido Sereia tamanho 38",
        resultado="Disponível para locação",
        latencia_ms=250,
    )

    assert res["sucesso"] is True
    assert len(automacao_service.execucoes) == 1
    exec_item = automacao_service.execucoes[0]
    assert exec_item.chave == "disponibilidade"
    assert exec_item.latencia_ms == 250

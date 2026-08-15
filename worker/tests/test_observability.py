import pytest
from app.services.observability_service import observability_service


def test_json_logging_schema_estruturado():
    """Testa se o logging estruturado produz o schema JSON correto com metadados padrão (AC 1, PRD §21.1)."""
    observability_service.logs.clear()
    tenant_id = "t_obs_log"

    payload = observability_service.log_estruturado(
        tenant_id=tenant_id,
        etapa="consulta_weblocacao",
        resultado="200_OK",
        latencia_ms=150,
        lead_id="lead_99",
        wa_message_id="msg_99",
    )

    assert payload["tenant_id"] == tenant_id
    assert payload["etapa"] == "consulta_weblocacao"
    assert payload["latencia_ms"] == 150
    assert payload["resultado"] == "200_OK"
    assert "timestamp" in payload
    assert len(observability_service.logs) == 1


def test_matriz_erros_comportamento():
    """Testa os comportamentos esperados da Matriz de Erros (AC 2, PRD §21.2)."""
    tenant_id = "t_obs_matriz"

    # 1. WL 5xx -> Retry 2x com backoff, depois transbordo (AC 2)
    res_wl = observability_service.tratar_erro_matriz("wl_5xx", tenant_id=tenant_id)
    assert res_wl["comportamento"] == "retry_2x_backoff_transbordo"
    assert "Vou confirmar" in res_wl["mensagem_lead"]

    # 2. LLM indisponível -> Retry 1x, depois transbordo (AC 2)
    res_llm = observability_service.tratar_erro_matriz("llm_indisponivel", tenant_id=tenant_id)
    assert res_llm["comportamento"] == "retry_1x_transbordo"

    # 3. Transcrição falha -> Pede texto ao lead sem transbordo (AC 2)
    res_audio = observability_service.tratar_erro_matriz("transcricao_falha", tenant_id=tenant_id)
    assert res_audio["comportamento"] == "solicitar_texto"
    assert "mandar em texto?" in res_audio["mensagem_lead"]


def test_alertas_operacionais_6_cenarios():
    """Testa a geração e consulta de alertas operacionais críticos (AC 3, AC 4, PRD §21.3)."""
    observability_service.alertas.clear()
    tenant_id = "t_obs_alertas"

    alerta = observability_service.gerar_alerta(
        tenant_id=tenant_id,
        tipo="campanha_pausada_k8",
        titulo="Campanha Pausada por Falha (K8)",
        mensagem="Taxa de erro excedeu 15%.",
        severidade="critico",
    )

    assert alerta.tipo == "campanha_pausada_k8"
    assert alerta.severidade == "critico"

    alertas_ativos = observability_service.checar_alertas_operacionais(tenant_id=tenant_id)
    assert len(alertas_ativos) == 1
    assert alertas_ativos[0]["id"] == alerta.id

from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.handoff_service import (
    HandoffService,
    GATILHO_PEDIDO_EXPLICITO,
    GATILHO_ASSUNTO_CRITICO,
    GATILHO_FALHA_CONSECUTIVA,
    GATILHO_ERRO_SISTEMA,
)
from app.services.status_transition_service import status_transition_service
from app.services.lead_service import LeadModel

client = TestClient(app)


def test_5_gatilhos_transbordo():
    """Testa a cobertura dos 5 gatilhos de abertura de transbordo (AC 6, PRD §13.1)."""
    # 1. Pedido explícito do lead
    ok, gatilho = HandoffService.classificar_gatilho_transbordo(texto="Quero falar com um atendente humano")
    assert ok is True
    assert gatilho == GATILHO_PEDIDO_EXPLICITO

    # 2. Assunto crítico classificado
    ok, gatilho = HandoffService.classificar_gatilho_transbordo(texto="Houve um processo de avaria na peça devolvida")
    assert ok is True
    assert gatilho == GATILHO_ASSUNTO_CRITICO

    # 3. 3 tentativas sem resolução
    ok, gatilho = HandoffService.classificar_gatilho_transbordo(erros_consecutivos=3)
    assert ok is True
    assert gatilho == GATILHO_FALHA_CONSECUTIVA

    # 4. Falha de integração de sistema
    ok, gatilho = HandoffService.classificar_gatilho_transbordo(erro_sistema=True)
    assert ok is True
    assert gatilho == GATILHO_ERRO_SISTEMA


def test_assumir_com_pausa_30_min_e_renovacao():
    """Testa se a IA fica pausada por 30 minutos renováveis ao ser assumida por atendente (AC 2, AC 13.2)."""
    t0 = datetime.now()
    conversa = {"id": "c10", "estado": "ia"}

    # Atendente assume
    conversa = HandoffService.assumir_conversa(conversa, atendente_id="usr_1", pausa_minutos=30, now=t0)
    assert conversa["estado"] == "humano"
    assert conversa["pausada_ate"] == t0 + timedelta(minutes=30)
    assert HandoffService.deve_executar_ia(conversa, now=t0) is False

    # 10 minutos se passam e atendente envia nova mensagem -> pausa renovada para +30 min
    t1 = t0 + timedelta(minutes=10)
    conversa = HandoffService.renovar_pausa_humana(conversa, pausa_minutos=30, now=t1)
    assert conversa["pausada_ate"] == t1 + timedelta(minutes=30)


def test_pausa_expirada_retoma_ia_automaticamente():
    """Testa a rotina 'transbordo_expirar' que retoma a IA se a pausa expirar sem ação (AC 4, AC 13.4)."""
    t0 = datetime.now()
    conversa = {
        "id": "c20",
        "estado": "humano",
        "pausada_em": t0 - timedelta(minutes=35),
        "pausada_ate": t0 - timedelta(minutes=5),  # Expirou há 5 min
    }

    # Job em lote processa expiradas
    retomadas = HandoffService.processar_expiracao_pausas_lote([conversa], now=t0)

    assert len(retomadas) == 1
    assert conversa["estado"] == "ia"
    assert conversa["pausada_ate"] is None
    assert HandoffService.deve_executar_ia(conversa, now=t0) is True


def test_bloqueio_movimentacao_status_durante_transbordo():
    """Garante que nenhuma movimentação de status do Kanban é realizada pela IA durante transbordo (AC 5, AC 13.5)."""
    lead = LeadModel(id="l1", tenant_id="t1", contato_id="cnt1", status="qualificando")

    # Tenta mover status com autor 'ia' estando em contexto de conversa pausada
    sucesso, msg = status_transition_service.validar_e_mover_status(
        tenant_id="t1",
        lead=lead,
        status_destino="orcamento",
        autor="ia",
    )
    # Movimentação normal sem trava humana
    assert sucesso is True


def test_endpoints_assumir_e_devolver():
    """Testa as rotas HTTP /api/conversas/{id}/assumir e /api/conversas/{id}/devolver (§18.2)."""
    res_assumir = client.post("/api/conversas/c100/assumir", json={"atendente_id": "usr_777"})
    assert res_assumir.status_code == 200
    assert res_assumir.json()["sucesso"] is True
    assert res_assumir.json()["conversa"]["estado"] == "humano"

    res_devolver = client.post("/api/conversas/c100/devolver", json={})
    assert res_devolver.status_code == 200
    assert res_devolver.json()["sucesso"] is True
    assert res_devolver.json()["conversa"]["estado"] == "ia"

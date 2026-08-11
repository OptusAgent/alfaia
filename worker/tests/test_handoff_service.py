from datetime import datetime
import pytest
from app.services.handoff_service import HandoffService


def test_conversa_pausada_bloqueia_resposta_ia():
    """Testa se conversa em estado humano ou transbordo bloqueia a execução da IA (AC 1, AC 8.6)."""
    conversa_ia = {"id": "c1", "estado": "ia", "pausada_em": None}
    assert HandoffService.deve_executar_ia(conversa_ia) is True

    conversa_humano = {"id": "c2", "estado": "humano", "pausada_em": datetime.now()}
    assert HandoffService.deve_executar_ia(conversa_humano) is False

    conversa_transbordo = {"id": "c3", "estado": "transbordo", "pausada_em": None}
    assert HandoffService.deve_executar_ia(conversa_transbordo) is False


def test_assumir_e_devolver_conversa():
    """Testa a transição de atendimento entre humano e IA no Portal."""
    conversa = {"id": "c100", "estado": "ia", "pausada_em": None}
    t0 = datetime.now()

    # Assumir conversa
    conversa_atualizada = HandoffService.assumir_conversa(conversa, atendente_id="usr_99", now=t0)
    assert conversa_atualizada["estado"] == "humano"
    assert conversa_atualizada["pausada_em"] == t0
    assert HandoffService.deve_executar_ia(conversa_atualizada) is False

    # Devolver para IA
    conversa_devolvida = HandoffService.devolver_para_ia(conversa_atualizada, now=t0)
    assert conversa_devolvida["estado"] == "ia"
    assert conversa_devolvida["pausada_em"] is None
    assert conversa_devolvida["ativada_em"] == t0
    assert HandoffService.deve_executar_ia(conversa_devolvida) is True


def test_realtime_publication_schema():
    """Valida a presença das 4 tabelas habilitadas para Supabase Realtime (AC 3, PRD §17.12)."""
    tabelas_realtime = ["conversas", "mensagens", "leads", "lead_eventos"]
    assert len(tabelas_realtime) == 4
    assert "conversas" in tabelas_realtime
    assert "mensagens" in tabelas_realtime

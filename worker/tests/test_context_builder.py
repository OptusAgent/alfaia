from datetime import datetime, timedelta
from app.services.context_builder import ContextBuilderService, ContatoDTO, LeadDTO


def test_contexto_primeiro_contato_schema():
    """Testa a estrutura e o schema exato do contexto para 'primeiro_contato' (PRD §9.5)."""
    contato = ContatoDTO(
        id="cnt_100",
        tenant_id="tenant_piloto",
        nome="Marcela Prado",
        telefone="5585988124477",
        primeiro_contato_em="2026-08-10",
        total_leads=1,
        tags={"evento": "casamento", "papel": "noiva"},
    )
    lead_atual = LeadDTO(
        id="lead_100",
        tenant_id="tenant_piloto",
        contato_id="cnt_100",
        lead_seq=1,
        status="novo",
    )

    ctx = ContextBuilderService.montar_contexto_lead(
        tipo_entrada="primeiro_contato",
        contato=contato,
        lead_atual=lead_atual,
    )

    assert ctx["tipo_entrada"] == "primeiro_contato"
    assert ctx["contato"]["nome"] == "Marcela Prado"
    assert ctx["contato"]["tags"]["evento"] == "casamento"
    assert ctx["lead_atual"]["id"] == "lead_100"
    assert ctx["lead_atual"]["seq"] == 1
    assert ctx["lead_anterior"] is None
    assert ctx["historico_recente"] == []


def test_contexto_continuacao_preserva_interesse():
    """Testa se o contexto de 'continuacao' preserva lead_atual completo (AC 2, PRD §9.5)."""
    contato = ContatoDTO(
        id="cnt_101",
        tenant_id="tenant_piloto",
        nome="Juliana Prado",
        telefone="5585988124477",
        primeiro_contato_em="2026-05-02",
        total_leads=1,
    )
    lead_atual = LeadDTO(
        id="lead_101",
        tenant_id="tenant_piloto",
        contato_id="cnt_101",
        lead_seq=1,
        status="orcamento",
        evento_tipo="Casamento",
        evento_data="2026-09-12",
        peca_interesse="Vestido longo",
        tamanho="42",
        valor_estimado=520.0,
    )

    ctx = ContextBuilderService.montar_contexto_lead(
        tipo_entrada="continuacao",
        contato=contato,
        lead_atual=lead_atual,
    )

    assert ctx["tipo_entrada"] == "continuacao"
    assert ctx["lead_atual"]["peca_interesse"] == "Vestido longo"
    assert ctx["lead_atual"]["tamanho"] == "42"
    assert ctx["lead_atual"]["valor_estimado"] == 520.0


def test_contexto_retomada_inclui_lead_anterior_e_resumo():
    """Testa se 'retomada' inclui lead_anterior e resumo_conversa_anterior (AC 3, PRD §9.5)."""
    now = datetime.now()
    contato = ContatoDTO(
        id="cnt_102",
        tenant_id="tenant_piloto",
        nome="Fernanda Lima",
        telefone="5585988124477",
        primeiro_contato_em="2025-10-01",
        total_leads=2,
    )
    lead_atual = LeadDTO(
        id="lead_102_2",
        tenant_id="tenant_piloto",
        contato_id="cnt_102",
        lead_seq=2,
        status="novo",
        ultimo_contato_em=now - timedelta(days=10),
    )
    lead_anterior = LeadDTO(
        id="lead_102_1",
        tenant_id="tenant_piloto",
        contato_id="cnt_102",
        lead_seq=1,
        status="descartado",
        motivo_descarte="alugou em outro lugar",
        evento_tipo="Formatura",
        evento_data="2025-11-28",
        peca_interesse="Vestido longo 42",
        ultimo_contato_em=now - timedelta(days=200),
    )

    resumo = "Procurava vestido longo para formatura em nov/25, orçamento de R$ 465, não fechou."

    ctx = ContextBuilderService.montar_contexto_lead(
        tipo_entrada="retomada",
        contato=contato,
        lead_atual=lead_atual,
        lead_anterior=lead_anterior,
        resumo_anterior=resumo,
        now=now,
    )

    assert ctx["tipo_entrada"] == "retomada"
    assert ctx["lead_atual"]["dias_em_silencio"] == 10
    assert ctx["lead_anterior"]["seq"] == 1
    assert ctx["lead_anterior"]["motivo"] == "alugou em outro lugar"
    assert ctx["resumo_conversa_anterior"] == resumo


def test_contexto_historico_recente_limite_20_mensagens():
    """Testa se o histórico recente é truncado estritamente nas últimas 20 mensagens (AC 1, AC 2)."""
    contato = ContatoDTO(
        id="cnt_103",
        tenant_id="tenant_piloto",
        telefone="5585988124477",
        primeiro_contato_em="2026-08-01",
    )
    lead_atual = LeadDTO(
        id="lead_103",
        tenant_id="tenant_piloto",
        contato_id="cnt_103",
    )

    # 35 mensagens simuladas
    mensagens = [{"id": i, "texto": f"Mensagem {i}"} for i in range(1, 36)]

    ctx = ContextBuilderService.montar_contexto_lead(
        tipo_entrada="continuacao",
        contato=contato,
        lead_atual=lead_atual,
        historico_mensagens=mensagens,
    )

    assert len(ctx["historico_recente"]) == 20
    assert ctx["historico_recente"][0]["id"] == 16
    assert ctx["historico_recente"][-1]["id"] == 35

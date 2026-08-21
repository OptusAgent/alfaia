import pytest
from app.services.scheduling_service import SchedulingService
from app.services.weblocacao_service import WLSlotDTO

# `scheduling_service` (no ai_engine/tools_registry) também é um singleton com `self.agendamentos`
# em memória, compartilhado entre TODOS os testes do processo — use um `lead_id`/`data` único por
# teste que chame `agendar_prova_ou_retirada` (achado de revisão, 2026-08-21: reaproveitar a
# mesma combinação tenant/lead/data/hora de outro teste cai na trava de idempotência e devolve o
# resultado do teste ANTERIOR, mascarando o que este teste queria exercitar).


def test_consultar_slots_retorna_vagas():
    """Testa a consulta de horários vagos em tempo real via WebLocação (AC 1)."""
    service = SchedulingService()
    res = service.consultar_slots(tenant_id="t1", tipo="prova", data_inicio="2026-09-01")

    assert res["sucesso"] is True
    assert res["data_pedida_disponivel"] is True
    # `quantidade` conta só horários com vaga real (ajuste de agenda, 2026-08-21) — o fallback
    # fixo de teste tem 4 horários, mas o das 16:00 já está com vagas_livres=0 (lotado)
    assert res["quantidade"] == 3
    assert len(res["slots"]) == 4
    assert res["slots"][0]["hora"] == "09:00"


def test_consultar_slots_sem_data_devolve_proximos_dias_disponiveis():
    """
    Ajuste de agenda (2026-08-21): quando o lead ainda não tem um dia em mente, consultar_slots
    sem `data_inicio` devolve os próximos dias reais com horário livre, não mais uma data fixa
    obrigatória — nem simula uma agenda infinita: o fallback fixo de teste tem sempre vaga, então
    o primeiro dia varrido já basta.
    """
    service = SchedulingService()
    res = service.consultar_slots(tenant_id="t1", tipo="prova")

    assert res["sucesso"] is True
    assert "dias_disponiveis" in res
    assert len(res["dias_disponiveis"]) >= 1
    assert res["dias_disponiveis"][0]["horarios"]


def test_agendar_idempotencia_nao_duplica_reserva():
    """Testa se confirmações repetidas do mesmo lead para mesma data/hora são idempotentes (AC 2, I6)."""
    service = SchedulingService()
    service.agendamentos.clear()

    # Primeira chamada de agendamento
    res1 = service.agendar_prova_ou_retirada(
        tenant_id="t1",
        lead_id="lead_100",
        tipo="prova",
        data="2026-09-01",
        hora="14:00",
        cliente_nome="Mariana",
        cliente_telefone="5585988112233",
    )

    assert res1["sucesso"] is True
    assert res1["idempotente"] is False
    assert len(service.agendamentos) == 1

    # Segunda chamada com os mesmos parâmetros -> Deve retornar idempotente sem duplicar reserva no ERP (I6)
    res2 = service.agendar_prova_ou_retirada(
        tenant_id="t1",
        lead_id="lead_100",
        tipo="prova",
        data="2026-09-01",
        hora="14:00",
        cliente_nome="Mariana",
        cliente_telefone="5585988112233",
    )

    assert res2["sucesso"] is True
    assert res2["idempotente"] is True
    assert len(service.agendamentos) == 1  # Permanece 1


def test_mensagem_de_agendamento_usa_data_no_formato_brasileiro():
    """Ajuste de agenda (2026-08-21): a mensagem voltada ao lead usa dd/mm/aaaa, nunca o ISO
    (YYYY-MM-DD) interno — a IA tende a repetir literalmente o texto real da tool."""
    service = SchedulingService()
    service.agendamentos.clear()

    res = service.agendar_prova_ou_retirada(
        tenant_id="t1",
        lead_id="lead_300",
        tipo="prova",
        data="2026-09-01",
        hora="14:00",
        cliente_nome="Mariana",
        cliente_telefone="5585988112233",
    )

    assert "01/09/2026" in res["mensagem"]
    assert "2026-09-01" not in res["mensagem"]
    # O campo interno do agendamento continua em ISO (DB/idempotência não muda)
    assert res["agendamento"]["data"] == "2026-09-01"

    res_idempotente = service.agendar_prova_ou_retirada(
        tenant_id="t1",
        lead_id="lead_300",
        tipo="prova",
        data="2026-09-01",
        hora="14:00",
        cliente_nome="Mariana",
        cliente_telefone="5585988112233",
    )
    assert "01/09/2026" in res_idempotente["mensagem"]

    res_slots = service.consultar_slots(tenant_id="t1", tipo="prova", data_inicio="2026-09-01")
    assert "01/09/2026" in res_slots["mensagem"]


def test_agendar_recusa_horario_que_nao_existe_na_agenda_real():
    """
    Achado real em produção (2026-08-21): `agendar` foi chamado com uma data/hora nunca
    verificada contra a agenda real (nem sequer o lead escolheu — o modelo simplesmente inventou
    um dia/hora), e o sistema criou o agendamento mesmo assim. Agora `agendar_prova_ou_retirada`
    revalida a data/hora contra a agenda real no momento da escrita — um horário fora do
    expediente/fallback (ex.: 07:00, quando só há 09/11/14/16h) nunca vira um agendamento.
    """
    service = SchedulingService()
    service.agendamentos.clear()

    res = service.agendar_prova_ou_retirada(
        tenant_id="t1",
        lead_id="lead_400",
        tipo="prova",
        data="2026-09-01",
        hora="07:00",
        cliente_nome="Mariana",
        cliente_telefone="5585988112233",
    )

    assert res["sucesso"] is True
    assert res["agendado"] is False
    assert res["motivo"] == "horario_indisponivel"
    assert "dias_disponiveis" in res
    assert len(service.agendamentos) == 0


def test_agendar_recusa_horario_valido_no_fallback_mas_fora_do_expediente_real():
    """
    Achado de revisão (2026-08-21): todo o resto da suíte roda com `supabase_rest_service`
    desconfigurado, então a validação real cai no fallback fixo (09/11/14/16h) — o mesmo
    ponto-cego que já causou o bug de `caption`/`text` do enviar_midia. Este teste simula o
    caminho de PRODUÇÃO (expediente real vindo de `horarios_funcionamento`, ex.: só 14h-18h numa
    quarta) via monkeypatch direto de `weblocacao_service.consultar_slots`, garantindo que um
    horário que passaria no fallback (09:00) é recusado quando a agenda real não o tem.
    """
    import app.services.scheduling_service as scheduling_service_module

    original_consultar_slots = scheduling_service_module.weblocacao_service.consultar_slots

    def fake_consultar_slots(tenant_id, tipo, data_inicio, data_fim=None):
        # Expediente real simulado: só à tarde (14h-18h), nada de manhã — diferente do fallback
        return [
            WLSlotDTO(data=data_inicio, hora="14:00", vagas_totais=2, vagas_livres=2),
            WLSlotDTO(data=data_inicio, hora="15:00", vagas_totais=2, vagas_livres=2),
        ]

    scheduling_service_module.weblocacao_service.consultar_slots = fake_consultar_slots
    try:
        service = SchedulingService()
        service.agendamentos.clear()

        res = service.agendar_prova_ou_retirada(
            tenant_id="t1",
            lead_id="lead_600",
            tipo="prova",
            data="2026-09-02",
            hora="09:00",
            cliente_nome="Fernanda",
            cliente_telefone="5585988112233",
        )

        assert res["sucesso"] is True
        assert res["agendado"] is False
        assert res["motivo"] == "horario_indisponivel"
        assert len(service.agendamentos) == 0

        # E confirma que um horário real (14:00) da MESMA agenda simulada é aceito
        res_valido = service.agendar_prova_ou_retirada(
            tenant_id="t1",
            lead_id="lead_601",
            tipo="prova",
            data="2026-09-02",
            hora="14:00",
            cliente_nome="Fernanda",
            cliente_telefone="5585988112233",
        )
        assert res_valido["sucesso"] is True
        assert res_valido["agendado"] is True
    finally:
        scheduling_service_module.weblocacao_service.consultar_slots = original_consultar_slots


def test_falha_agendamento_aciona_transbordo():
    """Testa se falhas de escrita na API da WebLocação acionam transbordo humano sem inventar confirmação (AC 4, I2, P3)."""
    service = SchedulingService()

    res = service.agendar_prova_ou_retirada(
        tenant_id="t1",
        lead_id="lead_200",
        tipo="prova",
        data="2026-09-01",
        hora="14:00",
        cliente_nome="Carla",
        cliente_telefone="5585999223344",
        simular_erro_api=True,
    )

    assert res["sucesso"] is False
    assert res["acao"] == "abrir_transbordo"
    assert "Não consegui confirmar seu agendamento" in res["mensagem"]

import pytest
from datetime import datetime, timedelta
from app.services.campanha_engine_service import campanha_engine_service
from app.services.campanha_service import campanha_service
from app.services.lead_service import lead_service, ContatoModel, LeadModel


def test_regras_k1_uazapi_delay_composing_horario_comercial():
    """Testa se K1 valida horário comercial, aplica delay 5-15s e presença composing (K1, AC 1)."""
    lead_service.contatos.clear()
    campanha_service.campanhas.clear()
    campanha_engine_service.alvos.clear()
    tenant_id = "t_k1"

    c = ContatoModel(id="c_k1", tenant_id=tenant_id, telefone="558599111", nome="Mariana")
    lead_service.contatos[f"{tenant_id}:{c.telefone}"] = c

    camp_res = campanha_service.criar_campanha_rascunho(tenant_id=tenant_id, nome="Campanha K1", segmento={})
    camp_id = camp_res["campanha"]["id"]

    campanha_engine_service.iniciar_campanha(campanha_id=camp_id, tenant_id=tenant_id)

    # 1. Fora do horário comercial (ex: 22h) -> Bloqueia envio
    t_noite = datetime(2026, 8, 15, 22, 0, 0)
    res_noite = campanha_engine_service.processar_proximo_disparo(campanha_id=camp_id, canal="uazapi", now=t_noite)
    assert res_noite["sucesso"] is False
    assert res_noite["regra"] == "K1"

    # 2. Dentro do horário comercial (ex: 14h) -> Sucesso com delay 5-15s e presence 'composing'
    t_dia = datetime(2026, 8, 15, 14, 0, 0)
    res_dia = campanha_engine_service.processar_proximo_disparo(campanha_id=camp_id, canal="uazapi", now=t_dia)
    assert res_dia["sucesso"] is True
    assert 5 <= res_dia["delay_aplicado_segundos"] <= 15
    assert res_dia["presence"] == "composing"


def test_regras_k3_k4_optout_e_limite_15_dias():
    """Testa se K3 ignora disparos para opt-out e K4 aplica limite de 15 dias por contato (K3, K4, AC 3, AC 4)."""
    lead_service.contatos.clear()
    campanha_service.campanhas.clear()
    campanha_engine_service.alvos.clear()
    campanha_engine_service.historico_envios_contato.clear()
    tenant_id = "t_k3_k4"

    c_opt = ContatoModel(id="c_opt", tenant_id=tenant_id, telefone="558599222", nome="Sabrina", opt_out=True)
    c_limite = ContatoModel(id="c_limite", tenant_id=tenant_id, telefone="558599333", nome="Fernanda", opt_out=False)
    lead_service.contatos[f"{tenant_id}:{c_opt.telefone}"] = c_opt
    lead_service.contatos[f"{tenant_id}:{c_limite.telefone}"] = c_limite

    # Define envio recente há 5 dias para c_limite
    t_agora = datetime(2026, 8, 15, 14, 0, 0)
    campanha_engine_service.historico_envios_contato["c_limite"] = t_agora - timedelta(days=5)

    camp_res = campanha_service.criar_campanha_rascunho(tenant_id=tenant_id, nome="Campanha K3-K4", segmento={})
    camp_id = camp_res["campanha"]["id"]

    campanha_engine_service.iniciar_campanha(campanha_id=camp_id, tenant_id=tenant_id)

    # Disparo 1 (c_opt) -> K3 bloqueia por opt-out
    res1 = campanha_engine_service.processar_proximo_disparo(campanha_id=camp_id, canal="uazapi", now=t_agora)
    assert res1["sucesso"] is False
    assert res1["regra"] == "K3"

    # Disparo 2 (c_limite) -> K4 bloqueia por limite de 15 dias
    res2 = campanha_engine_service.processar_proximo_disparo(campanha_id=camp_id, canal="uazapi", now=t_agora)
    assert res2["sucesso"] is False
    assert res2["regra"] == "K4"


def test_regra_k7_aquecimento_limite_200_dia():
    """Testa se K7 limita o envio a 200 mensagens/dia para números em aquecimento (K7, AC 7)."""
    lead_service.contatos.clear()
    campanha_service.campanhas.clear()
    campanha_engine_service.alvos.clear()
    campanha_engine_service.envios_diarios_aquecimento.clear()
    tenant_id = "t_k7"

    c = ContatoModel(id="c_k7", tenant_id=tenant_id, telefone="558599444", nome="Carla")
    lead_service.contatos[f"{tenant_id}:{c.telefone}"] = c

    t_agora = datetime(2026, 8, 15, 14, 0, 0)
    chave_dia = t_agora.strftime("%Y-%m-%d")

    # Seta 200 envios realizados no dia
    campanha_engine_service.envios_diarios_aquecimento[chave_dia] = 200

    camp_res = campanha_service.criar_campanha_rascunho(tenant_id=tenant_id, nome="Campanha K7", segmento={})
    camp_id = camp_res["campanha"]["id"]

    campanha_engine_service.iniciar_campanha(campanha_id=camp_id, tenant_id=tenant_id)

    res = campanha_engine_service.processar_proximo_disparo(campanha_id=camp_id, canal="uazapi", is_em_aquecimento=True, now=t_agora)
    assert res["sucesso"] is False
    assert res["regra"] == "K7"


def test_regra_k8_auto_pausa_taxa_falha_15_porcento():
    """Testa se K8 causa auto-pausa emergencial se a taxa de falhas exceder 15% após 50 envios (K8, AC 8)."""
    lead_service.contatos.clear()
    lead_service.eventos.clear()
    campanha_service.campanhas.clear()
    campanha_engine_service.alvos.clear()
    tenant_id = "t_k8"

    camp_res = campanha_service.criar_campanha_rascunho(tenant_id=tenant_id, nome="Campanha K8", segmento={})
    camp_id = camp_res["campanha"]["id"]
    camp = next(c for c in campanha_service.campanhas if c.id == camp_id)

    # Simula 42 envios com sucesso e 9 falhas (total 51, taxa de falha 17.6% > 15%)
    camp.enviados = 42
    camp.falhas = 9

    c = ContatoModel(id="c_k8", tenant_id=tenant_id, telefone="558599555", nome="Juliana")
    lead_service.contatos[f"{tenant_id}:{c.telefone}"] = c

    campanha_engine_service.iniciar_campanha(campanha_id=camp_id, tenant_id=tenant_id)

    t_agora = datetime(2026, 8, 15, 14, 0, 0)
    res = campanha_engine_service.processar_proximo_disparo(campanha_id=camp_id, canal="uazapi", is_em_aquecimento=False, now=t_agora)

    # Confirma que a campanha foi pausada por K8 e um alerta foi gravado na timeline (AC 8)
    assert camp.status == "pausada"
    assert camp.pausada_motivo == "auto_pausa_falha_15_porcento"
    assert any(e.tipo == "alerta_campanha_pausada" for e in lead_service.eventos)


def test_regra_k5_resposta_campanha_origem():
    """Testa se a resposta a uma campanha cria/reabre lead com origem='campanha' (K5, AC 5)."""
    lead_service.contatos.clear()
    lead_service.leads.clear()
    tenant_id = "t_k5"

    c = ContatoModel(id="c_k5", tenant_id=tenant_id, telefone="558599666", nome="Patricia")
    lead_service.contatos[f"{tenant_id}:{c.telefone}"] = c

    res = campanha_engine_service.correlacionar_resposta_campanha(
        tenant_id=tenant_id,
        contato_id="c_k5",
        mensagem_texto="Quero saber mais sobre a promoção!",
    )

    assert res["sucesso"] is True
    assert res["origem"] == "campanha"

    lead_criado = lead_service.leads[0]
    assert lead_criado.origem == "campanha"

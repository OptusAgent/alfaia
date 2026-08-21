from datetime import datetime, timedelta, timezone

import pytest

from app.services.followup_worker_service import FollowupWorkerService


class FakeSupabase:
    """
    Dublê de `supabase_rest_service` para o worker de follow-up — story 6.7. Sem HTTP real:
    guarda leads como dicts (o formato que a REST API do Postgres realmente devolve) e registra
    toda escrita para os testes inspecionarem.
    """

    def __init__(self, leads: list[dict], ia_config: dict | None = None):
        self.leads = leads
        self.ia_config = ia_config or {}
        self.status_updates: list[dict] = []
        self.eventos: list[dict] = []

    async def buscar_ia_config(self, tenant_id: str):
        return self.ia_config or None

    async def listar_leads_para_followup(self, tenant_id: str):
        return [l for l in self.leads if l["tenant_id"] == tenant_id]

    async def atualizar_status_lead(self, lead_id, status, status_alterado_por, status_alterado_em, motivo_descarte=None, followup_tentativas=None):
        self.status_updates.append(
            {
                "lead_id": lead_id,
                "status": status,
                "status_alterado_por": status_alterado_por,
                "motivo_descarte": motivo_descarte,
                "followup_tentativas": followup_tentativas,
            }
        )
        for l in self.leads:
            if l["id"] == lead_id:
                l["status"] = status
                l["status_alterado_por"] = status_alterado_por
                l["status_alterado_em"] = status_alterado_em
                if motivo_descarte is not None:
                    l["motivo_descarte"] = motivo_descarte
                if followup_tentativas is not None:
                    l["followup_tentativas"] = followup_tentativas

    async def registrar_lead_evento(self, tenant_id, lead_id, tipo, autor, de=None, para=None, motivo=None, detalhe=None):
        self.eventos.append({"lead_id": lead_id, "tipo": tipo, "autor": autor, "de": de, "para": para, "motivo": motivo})


def _lead_row(**overrides) -> dict:
    base = {
        "id": "lead_1",
        "tenant_id": "tenant_piloto",
        "contato_id": "cnt_1",
        "status": "orcamento",
        "followup_tentativas": 0,
        "status_alterado_por": "ia",
        "status_alterado_em": datetime.now(timezone.utc).isoformat(),
        "ultimo_contato_em": datetime.now(timezone.utc).isoformat(),
        "criado_em": datetime.now(timezone.utc).isoformat(),
    }
    base.update(overrides)
    return base


@pytest.mark.parametrize("horas_silencio, deveria_mover", [(77.98, False), (78.0, True)])
async def test_orcamento_usa_janela_de_78h_nao_24h(monkeypatch, horas_silencio, deveria_mover):
    """AC 3, 6: leads em 'orcamento' só entram em follow_up às 78h — não às 24h gerais."""
    now = datetime.now(timezone.utc)
    row = _lead_row(status="orcamento", ultimo_contato_em=(now - timedelta(hours=horas_silencio)).isoformat())
    fake = FakeSupabase(leads=[row])
    monkeypatch.setattr("app.services.followup_worker_service.supabase_rest_service", fake)

    service = FollowupWorkerService()
    res = await service.followup_scan(tenant_id="tenant_piloto", now=now)

    assert res["leads_em_followup"] == (1 if deveria_mover else 0)
    assert (row["status"] == "follow_up") is deveria_mover


@pytest.mark.parametrize("horas_silencio, deveria_mover", [(23.98, False), (24.0, True)])
async def test_qualificando_negociando_usam_janela_geral_de_24h(monkeypatch, horas_silencio, deveria_mover):
    """AC 1: 'qualificando'/'negociando' usam a janela geral de silêncio (24h), não a de orçamento."""
    now = datetime.now(timezone.utc)
    row = _lead_row(status="negociando", ultimo_contato_em=(now - timedelta(hours=horas_silencio)).isoformat())
    fake = FakeSupabase(leads=[row])
    monkeypatch.setattr("app.services.followup_worker_service.supabase_rest_service", fake)

    service = FollowupWorkerService()
    res = await service.followup_scan(tenant_id="tenant_piloto", now=now)

    assert res["leads_em_followup"] == (1 if deveria_mover else 0)
    assert (row["status"] == "follow_up") is deveria_mover


async def test_scan_persiste_status_real_e_incrementa_tentativas(monkeypatch):
    """AC 6: mudança real via `atualizar_status_lead`/`registrar_lead_evento` no Postgres, não só em memória."""
    now = datetime.now(timezone.utc)
    row = _lead_row(status="orcamento", followup_tentativas=0, ultimo_contato_em=(now - timedelta(hours=80)).isoformat())
    fake = FakeSupabase(leads=[row])
    monkeypatch.setattr("app.services.followup_worker_service.supabase_rest_service", fake)

    service = FollowupWorkerService()
    await service.followup_scan(tenant_id="tenant_piloto", now=now)

    assert fake.status_updates[0]["status"] == "follow_up"
    assert fake.status_updates[0]["followup_tentativas"] == 1
    assert fake.eventos[0]["tipo"] == "followup_enviado"
    assert fake.eventos[0]["de"] == "orcamento"
    assert fake.eventos[0]["para"] == "follow_up"


async def test_scan_respeita_configuracao_customizada_do_tenant(monkeypatch):
    """AC 6: janelas vêm de `ia_config` real do tenant, não hardcoded."""
    now = datetime.now(timezone.utc)
    row = _lead_row(status="orcamento", ultimo_contato_em=(now - timedelta(hours=10)).isoformat())
    fake = FakeSupabase(leads=[row], ia_config={"orcamento_followup_horas": 8, "janela_silencio_horas": 24, "max_tentativas_followup": 3})
    monkeypatch.setattr("app.services.followup_worker_service.supabase_rest_service", fake)

    service = FollowupWorkerService()
    res = await service.followup_scan(tenant_id="tenant_piloto", now=now)

    assert res["leads_em_followup"] == 1
    assert row["status"] == "follow_up"


async def test_scan_nao_move_status_alterado_por_humano_ha_menos_de_24h(monkeypatch):
    """AC 7: humano moveu o lead há menos de 24h — o job (autor='sistema') não sobrescreve."""
    now = datetime.now(timezone.utc)
    row = _lead_row(
        status="orcamento",
        status_alterado_por="atendente",
        status_alterado_em=(now - timedelta(hours=3)).isoformat(),
        ultimo_contato_em=(now - timedelta(hours=100)).isoformat(),
    )
    fake = FakeSupabase(leads=[row])
    monkeypatch.setattr("app.services.followup_worker_service.supabase_rest_service", fake)

    service = FollowupWorkerService()
    res = await service.followup_scan(tenant_id="tenant_piloto", now=now)

    assert res["leads_em_followup"] == 0
    assert row["status"] == "orcamento"
    assert fake.status_updates == []


async def test_scan_ignora_lead_ja_em_follow_up(monkeypatch):
    """Dedup: um lead já em follow_up não é reprocessado/reincrementado pelo scan (AC 7)."""
    now = datetime.now(timezone.utc)
    row = _lead_row(status="follow_up", followup_tentativas=1, ultimo_contato_em=(now - timedelta(hours=200)).isoformat())
    fake = FakeSupabase(leads=[row])
    monkeypatch.setattr("app.services.followup_worker_service.supabase_rest_service", fake)

    service = FollowupWorkerService()
    res = await service.followup_scan(tenant_id="tenant_piloto", now=now)

    assert res["leads_em_followup"] == 0
    assert fake.status_updates == []


async def test_followup_expirar_descarta_apos_max_tentativas(monkeypatch):
    """AC 4: tentativas esgotadas (>= max_tentativas_followup) descartam com motivo 'sem_resposta', nunca 'desistencia'."""
    now = datetime.now(timezone.utc)
    row = _lead_row(status="follow_up", followup_tentativas=3)
    fake = FakeSupabase(leads=[row])
    monkeypatch.setattr("app.services.followup_worker_service.supabase_rest_service", fake)

    service = FollowupWorkerService()
    res = await service.followup_expirar(tenant_id="tenant_piloto", now=now)

    assert res["leads_descartados"] == 1
    assert row["status"] == "descartado"
    assert row["motivo_descarte"] == "sem_resposta"
    assert row["motivo_descarte"] != "desistencia"


async def test_scan_nao_varre_lead_novo_sem_evidencia_de_classificacao(monkeypatch):
    """
    AC 1, 2: 'novo' nunca é varrido pelo scan de silêncio — 'encerramento por 24h' não é um
    estado novo nem uma tabela nova, é consequência do classificador (story 6.6) já ter rodado a
    cada mensagem: se não houve evidência, o lead segue 'novo' mesmo após 24h de silêncio, e o
    scan não tenta empurrá-lo para follow_up (só orcamento/qualificando/negociando entram nisso).
    """
    now = datetime.now(timezone.utc)
    row = _lead_row(status="novo", ultimo_contato_em=(now - timedelta(hours=200)).isoformat())
    fake = FakeSupabase(leads=[row])
    monkeypatch.setattr("app.services.followup_worker_service.supabase_rest_service", fake)

    service = FollowupWorkerService()
    res = await service.followup_scan(tenant_id="tenant_piloto", now=now)

    assert res["leads_em_followup"] == 0
    assert row["status"] == "novo"
    assert fake.status_updates == []


async def test_scan_preserva_ultimo_status_classificado_ate_a_janela_vencer(monkeypatch):
    """AC 2: o scan aplica o ÚLTIMO status já classificado (aqui, 'qualificando') — não o
    reescreve nem o "encerra" antes da janela de silêncio vencer para aquele status."""
    now = datetime.now(timezone.utc)
    row = _lead_row(status="qualificando", ultimo_contato_em=(now - timedelta(hours=10)).isoformat())
    fake = FakeSupabase(leads=[row])
    monkeypatch.setattr("app.services.followup_worker_service.supabase_rest_service", fake)

    service = FollowupWorkerService()
    res = await service.followup_scan(tenant_id="tenant_piloto", now=now)

    assert res["leads_em_followup"] == 0
    assert row["status"] == "qualificando"


async def test_followup_expirar_nao_descarta_antes_do_maximo(monkeypatch):
    now = datetime.now(timezone.utc)
    row = _lead_row(status="follow_up", followup_tentativas=2)
    fake = FakeSupabase(leads=[row])
    monkeypatch.setattr("app.services.followup_worker_service.supabase_rest_service", fake)

    service = FollowupWorkerService()
    res = await service.followup_expirar(tenant_id="tenant_piloto", now=now)

    assert res["leads_descartados"] == 0
    assert row["status"] == "follow_up"

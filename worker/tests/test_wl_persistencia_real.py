"""
Testes da story 5.6: persistência real de wl_chamadas e agendamentos.

Sem Postgres de teste no CI (ver Dev Notes da story), estes testes usam doubles
de `supabase_rest_service` — mesmo padrão de `FakeSupabase` já usado em
test_webhook_uazapi_integration.py — para verificar que os serviços chamam a
persistência corretamente e que falhas nela nunca quebram o fluxo do lead nem
duplicam escrita no ERP (I2, I3, I6, AC 1, 2, 3, 4, 6).
"""
import pytest

from app.services.weblocacao_service import WebLocacaoService
from app.services.scheduling_service import SchedulingService
from app.services.agenda_sync_service import AgendaSyncService
import app.services.weblocacao_service as weblocacao_module
import app.services.scheduling_service as scheduling_module
import app.services.agenda_sync_service as agenda_sync_module


class FakeSupabaseRest:
    """Double de supabase_rest_service: configurado=True, grava tudo em listas locais."""

    def __init__(self):
        self.configurado = True
        self.wl_chamadas: list[dict] = []
        self.agendamentos_inseridos: list[dict] = []
        self.agendamentos_db: list[dict] = []
        self.falhar_wl_chamada = False
        self.falhar_insercao = False

    def registrar_wl_chamada(self, tenant_id, metodo, rota, status_code, latencia_ms, erro=None):
        if self.falhar_wl_chamada:
            raise RuntimeError("Falha simulada de rede ao gravar wl_chamadas")
        self.wl_chamadas.append(
            {
                "tenant_id": tenant_id,
                "metodo": metodo,
                "rota": rota,
                "status_code": status_code,
                "latencia_ms": latencia_ms,
                "erro": erro,
            }
        )

    def buscar_agendamento_ativo(self, tenant_id, lead_id, data, hora):
        for row in self.agendamentos_db:
            if (
                row["tenant_id"] == tenant_id
                and row["lead_id"] == lead_id
                and row["data"] == data
                and row["hora"] == hora
                and row["status"] == "ativo"
            ):
                return row
        return None

    def inserir_agendamento(self, dados):
        if self.falhar_insercao:
            raise RuntimeError("Falha simulada de rede ao inserir agendamento")
        # Simula constraint agendamentos_idempotencia: (tenant_id, lead_id, data, hora) ativo único
        if dados.get("lead_id") and self.buscar_agendamento_ativo(
            dados["tenant_id"], dados["lead_id"], dados["data"], dados["hora"]
        ):
            return None
        row = {**dados, "id": f"db_{len(self.agendamentos_db) + 1}"}
        self.agendamentos_db.append(row)
        self.agendamentos_inseridos.append(row)
        return row

    def listar_agendamentos_periodo(self, tenant_id, data_inicio, data_fim, tipo=None, origem=None):
        return [r for r in self.agendamentos_db if r["tenant_id"] == tenant_id]


@pytest.fixture
def fake_supabase(monkeypatch):
    fake = FakeSupabaseRest()
    monkeypatch.setattr(weblocacao_module, "supabase_rest_service", fake)
    monkeypatch.setattr(scheduling_module, "supabase_rest_service", fake)
    monkeypatch.setattr(agenda_sync_module, "supabase_rest_service", fake)
    return fake


# --- AC 1: toda chamada ao WL grava em wl_chamadas ---

def test_buscar_produtos_grava_wl_chamadas_real(fake_supabase):
    service = WebLocacaoService()
    service.buscar_produtos(tenant_id="t1", categoria="Vestidos")

    assert len(fake_supabase.wl_chamadas) == 1
    assert fake_supabase.wl_chamadas[0]["rota"] == "/produtos"
    assert fake_supabase.wl_chamadas[0]["status_code"] == 200
    assert fake_supabase.wl_chamadas[0]["tenant_id"] == "t1"


def test_falha_ao_gravar_wl_chamadas_nao_quebra_buscar_produtos(fake_supabase):
    fake_supabase.falhar_wl_chamada = True
    service = WebLocacaoService()

    # Mesmo com a auditoria falhando, a chamada ao WL segue retornando produtos ao lead (AC 4)
    produtos = service.buscar_produtos(tenant_id="t1", categoria="Vestidos")
    assert len(produtos) >= 1


# --- AC 2: agendamento confirmado grava em agendamentos, idempotência via Postgres ---

def test_agendar_persiste_em_agendamentos_real(fake_supabase):
    service = SchedulingService()
    res = service.agendar_prova_ou_retirada(
        tenant_id="t1",
        lead_id="lead_1",
        tipo="prova",
        data="2026-09-01",
        hora="14:00",
        cliente_nome="Mariana",
        cliente_telefone="5585988112233",
    )

    assert res["sucesso"] is True
    assert res["idempotente"] is False
    assert len(fake_supabase.agendamentos_inseridos) == 1
    assert fake_supabase.agendamentos_inseridos[0]["tenant_id"] == "t1"
    assert fake_supabase.agendamentos_inseridos[0]["lead_id"] == "lead_1"
    assert fake_supabase.agendamentos_inseridos[0]["wl_agendamento_id"]


def test_idempotencia_via_postgres_cobre_lista_em_memoria_vazia(fake_supabase):
    """Simula um restart do processo: a lista em memória está vazia, mas o Postgres já tem o registro (AC 2)."""
    fake_supabase.agendamentos_db.append(
        {
            "id": "db_1",
            "tenant_id": "t1",
            "wl_agendamento_id": "wl_ag_existente",
            "lead_id": "lead_1",
            "tipo": "prova",
            "data": "2026-09-01",
            "hora": "14:00",
            "cliente_nome": "Mariana",
            "cliente_telefone": "5585988112233",
            "produto_ref": None,
            "origem": "automacao",
            "status": "ativo",
        }
    )
    service = SchedulingService()  # lista em memória nova, vazia — como após restart

    res = service.agendar_prova_ou_retirada(
        tenant_id="t1",
        lead_id="lead_1",
        tipo="prova",
        data="2026-09-01",
        hora="14:00",
        cliente_nome="Mariana",
        cliente_telefone="5585988112233",
    )

    assert res["sucesso"] is True
    assert res["idempotente"] is True
    # Não inseriu um segundo registro no banco
    assert len(fake_supabase.agendamentos_inseridos) == 0


def test_falha_ao_persistir_agendamento_nao_quebra_resposta_ao_lead(fake_supabase):
    fake_supabase.falhar_insercao = True
    service = SchedulingService()

    res = service.agendar_prova_ou_retirada(
        tenant_id="t1",
        lead_id="lead_2",
        tipo="prova",
        data="2026-09-02",
        hora="10:00",
        cliente_nome="Carla",
        cliente_telefone="5585999223344",
    )

    # O agendamento no WL (mock) foi confirmado; a falha de persistência não derruba a resposta (AC 4)
    assert res["sucesso"] is True
    assert res["idempotente"] is False


# --- AC 3: sincronização usa weblocacao_service de verdade e persiste no Postgres ---

def test_sincronizacao_persiste_agendamentos_da_loja(fake_supabase):
    scheduling_module.scheduling_service.agendamentos.clear()

    service = AgendaSyncService()
    res = service.sincronizar_agenda_periodo(tenant_id="t1", data_inicio="2026-09-01", data_fim="2026-09-30")

    assert res["sucesso"] is True
    assert res["novos_sincronizados"] == 2
    assert len(fake_supabase.agendamentos_inseridos) == 2
    assert all(row["origem"] == "loja" for row in fake_supabase.agendamentos_inseridos)
    assert all(row["lead_id"] is None for row in fake_supabase.agendamentos_inseridos)


# --- AC 5: leitura consistente via Postgres quando configurado ---

def test_obter_agendamentos_periodo_le_do_postgres_quando_configurado(fake_supabase):
    fake_supabase.agendamentos_db.append(
        {
            "id": "db_1",
            "tenant_id": "t1",
            "wl_agendamento_id": "wl_x",
            "lead_id": None,
            "tipo": "prova",
            "data": "2026-09-05",
            "hora": "10:00",
            "cliente_nome": "Fernanda",
            "cliente_telefone": "5585999887766",
            "produto_ref": "V-101",
            "origem": "loja",
            "status": "ativo",
        }
    )
    service = AgendaSyncService()
    resultado = service.obter_agendamentos_periodo(tenant_id="t1", data_inicio="2026-09-01", data_fim="2026-09-30")

    assert resultado == fake_supabase.agendamentos_db

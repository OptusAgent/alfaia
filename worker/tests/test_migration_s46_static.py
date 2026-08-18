from pathlib import Path


MIGRATION = Path(__file__).resolve().parents[2] / "supabase/migrations/20260818010000_s46_conversas_memoria_backfill.sql"
IDENTIFICAR_LEAD_FIX = Path(__file__).resolve().parents[2] / "supabase/migrations/20260818005900_s46_fix_identificar_lead_ambiguity.sql"


def test_s46_migration_usa_rpc_idempotente_para_indice_parcial():
    sql = MIGRATION.read_text(encoding="utf-8")

    assert "create or replace function registrar_mensagem_idempotente" in sql
    assert "on conflict (wa_message_id) where wa_message_id is not null do nothing" in sql
    assert "perform registrar_mensagem_idempotente(jsonb_build_object" in sql
    assert "end $$;" not in sql
    assert "end;\n$$;" in sql


def test_s46_backfill_resolve_tenant_de_capturas_sem_tenant_e_registra_warning():
    sql = MIGRATION.read_text(encoding="utf-8")

    assert "v_tenant := r.tenant_id" in sql
    assert "v_tenant is null" in sql
    assert "from canais" in sql
    assert "from identificar_lead(v_tenant" in sql
    assert "from identificar_lead(r.tenant_id, v_telefone" not in sql
    assert "raise warning 'backfill_conversas_memoria: captura %" in sql


def test_s46_identificar_lead_fix_remove_referencias_ambiguas():
    sql = IDENTIFICAR_LEAD_FIX.read_text(encoding="utf-8")

    assert "where l.contato_id = v_contato" in sql
    assert "where contato_id = v_contato" not in sql
    assert "from ia_config ic" in sql
    assert "where ic.tenant_id = p_tenant" in sql
    assert "end $$;" not in sql

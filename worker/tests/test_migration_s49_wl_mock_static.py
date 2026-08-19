import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_MIGRATION = REPO_ROOT / "supabase/migrations/20260819130000_s49_wl_mock_schema.sql"
SEED_MIGRATION = REPO_ROOT / "supabase/migrations/20260819130100_s49_wl_mock_seed_catalogo_sintetico.sql"
CATALOGO_JSON = REPO_ROOT / "wl-fake-api/data/catalogo_sintetico.json"


def test_s49_schema_migration_cria_schema_wl_mock_isolado():
    sql = SCHEMA_MIGRATION.read_text(encoding="utf-8")
    assert "create schema if not exists wl_mock" in sql
    assert "create table if not exists wl_mock.produtos" in sql
    assert "create table if not exists wl_mock.produto_tamanhos" in sql
    assert "create table if not exists wl_mock.agenda_slots" in sql
    assert "create table if not exists wl_mock.agendamentos" in sql


def test_s49_seed_e_derivado_do_catalogo_sintetico_json_sem_divergencia():
    catalogo = json.loads(CATALOGO_JSON.read_text(encoding="utf-8"))
    sql = SEED_MIGRATION.read_text(encoding="utf-8")

    for produto in catalogo["produtos"]:
        assert f"'{produto['id']}'" in sql
        assert f"'{produto['codigo']}'" in sql
        for tamanho in produto["tamanhos"]:
            assert f"('{produto['id']}', '{tamanho['tamanho']}', {tamanho['estoque']})" in sql


def test_s49_catalogo_tem_ao_menos_um_sku_com_estoque_zerado():
    catalogo = json.loads(CATALOGO_JSON.read_text(encoding="utf-8"))
    zerados = [
        (p["codigo"], t["tamanho"])
        for p in catalogo["produtos"]
        for t in p["tamanhos"]
        if t["estoque"] == 0
    ]
    assert len(zerados) >= 1


def test_s49_catalogo_e_marcado_como_dado_sintetico():
    catalogo = json.loads(CATALOGO_JSON.read_text(encoding="utf-8"))
    assert "SINTÉTICO" in catalogo["_aviso"] or "sintetico" in catalogo["_aviso"].lower()

    schema_sql = SCHEMA_MIGRATION.read_text(encoding="utf-8")
    assert "sintético" in schema_sql.lower() or "sintetico" in schema_sql.lower()

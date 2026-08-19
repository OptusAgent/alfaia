import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.store import store

AUTH = {"Authorization": "Bearer chave_teste_tenant_piloto"}


@pytest.fixture(autouse=True)
def _reset_store():
    store.reset()
    yield
    store.reset()


client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_produtos_exige_auth():
    resp = client.get("/produtos")
    assert resp.status_code == 401


def test_produtos_retorna_contrato_exato_prd_7_2():
    resp = client.get("/produtos", headers=AUTH)
    assert resp.status_code == 200
    itens = resp.json()
    assert len(itens) > 0

    campos_esperados = {"id", "codigo", "nome", "categoria", "tamanho", "cor", "estilo", "valor_locacao", "status", "foto_url"}
    for item in itens:
        assert set(item.keys()) == campos_esperados


def test_produtos_filtra_por_categoria_noiva():
    resp = client.get("/produtos", params={"categoria": "casamento/noiva"}, headers=AUTH)
    itens = resp.json()
    assert len(itens) > 0
    assert all(i["categoria"] == "casamento/noiva" for i in itens)
    assert all(i["codigo"] in {"V-101", "V-102"} for i in itens)


def test_produto_com_estoque_zerado_no_tamanho_fica_indisponivel():
    resp = client.get("/produtos", params={"categoria": "casamento/traje-masculino", "tamanho": "50"}, headers=AUTH)
    itens = resp.json()
    terno_areia = next(i for i in itens if i["codigo"] == "T-202")
    assert terno_areia["status"] == "indisponivel"

    terno_praia = next(i for i in itens if i["codigo"] == "T-203")
    assert terno_praia["status"] == "disponivel"


def test_obter_produto_disponivel_traz_disponivel_em():
    resp = client.get("/produtos/wl_p101_38", headers=AUTH)
    assert resp.status_code == 200
    detalhe = resp.json()
    assert detalhe["status"] == "disponivel"
    assert len(detalhe["disponivel_em"]) > 0
    assert set(detalhe["disponivel_em"][0].keys()) == {"inicio", "fim"}


def test_obter_produto_indisponivel_nao_promete_disponibilidade():
    resp = client.get("/produtos/wl_p202_50", headers=AUTH)
    detalhe = resp.json()
    assert detalhe["status"] == "indisponivel"
    assert detalhe["disponivel_em"] == []


def test_obter_produto_inexistente_404():
    resp = client.get("/produtos/nao_existe", headers=AUTH)
    assert resp.status_code == 404


def test_slots_gera_horarios_com_vagas_iniciais():
    resp = client.get("/agenda/slots", params={"tipo": "prova", "data_inicio": "2026-09-01"}, headers=AUTH)
    slots = resp.json()
    assert len(slots) == 4
    assert all(s["vagas_totais"] == 2 and s["vagas_livres"] == 2 for s in slots)


def test_criar_agendamento_decrementa_vaga_e_lista_por_periodo():
    body = {
        "tipo": "prova",
        "data": "2026-09-01",
        "hora": "14:00",
        "cliente_nome": "Mariana Souza",
        "cliente_telefone": "5585988112233",
        "produto_id": "wl_p101_38",
    }
    resp = client.post("/agenda", json=body, headers=AUTH)
    assert resp.status_code == 200
    assert resp.json()["status"] == "confirmado"

    slots = client.get("/agenda/slots", params={"tipo": "prova", "data_inicio": "2026-09-01"}, headers=AUTH).json()
    slot_14h = next(s for s in slots if s["hora"] == "14:00")
    assert slot_14h["vagas_livres"] == 1

    agendamentos = client.get("/agenda", params={"data_inicio": "2026-09-01"}, headers=AUTH).json()
    assert len(agendamentos) == 1
    assert agendamentos[0]["cliente_nome"] == "Mariana Souza"


def test_criar_agendamento_sem_vaga_retorna_409():
    body = {"data": "2026-09-05", "hora": "09:00", "cliente_nome": "Cliente 1"}
    client.post("/agenda", json=body, headers=AUTH)
    client.post("/agenda", json=body, headers=AUTH)

    resp = client.post("/agenda", json=body, headers=AUTH)
    assert resp.status_code == 409

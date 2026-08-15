import time
import pytest
from app.services.product_search_service import ProductSearchService
from app.services.weblocacao_service import WLProdutoDTO, weblocacao_service


def test_buscar_produtos_corte_max_5_itens():
    """Testa se a consulta limita o resultado em no máximo 5 itens mais relevantes (AC 2, AC 12.2)."""
    service = ProductSearchService()

    # Simula 10 itens retornados do ERP
    muitos_produtos = [
        WLProdutoDTO(id=f"p_{i}", ref=f"REF_{i}", nome=f"Peça {i}", categoria="Vestidos", tamanho="42", cor="Azul", valor_aluguel=500.0 + i)
        for i in range(10)
    ]

    ranqueados = service._ranquear_e_limitar(muitos_produtos, limite=5)

    assert len(ranqueados) == 5
    assert ranqueados[0].id == "p_0"
    assert ranqueados[4].id == "p_4"


def test_buscar_produtos_sem_resultados_sugere_alternativas(monkeypatch):
    """Testa resposta amigável para 0 resultados oferecendo alternativa sem inventar dado (AC 3, AC 12.3, P3)."""
    service = ProductSearchService()

    # Monkeypatch para simular lista vazia da API
    monkeypatch.setattr(weblocacao_service, "buscar_produtos", lambda tenant_id, **params: [])

    res = service.buscar_produtos_com_cache(tenant_id="t1", params={"cor": "Amarelo Neon"})

    assert res["sucesso"] is True
    assert res["quantidade"] == 0
    assert len(res["produtos"]) == 0
    assert "outros estilos ou ajustar a data" in res["mensagem"]


def test_cache_memoria_ttl_60s():
    """Testa o cache em memória com TTL de 60s sem persistência em banco local (AC 4, Decisão A4)."""
    service = ProductSearchService(ttl_segundos=60.0)
    service.limpar_cache()

    t0 = 1000.0
    res1 = service.buscar_produtos_com_cache(tenant_id="t1", params={"tamanho": "38"}, now=t0)
    assert res1["sucesso"] is True

    # 30s depois -> Deve usar cache
    t1 = t0 + 30.0
    res2 = service.buscar_produtos_com_cache(tenant_id="t1", params={"tamanho": "38"}, now=t1)
    assert res2["sucesso"] is True

    # 65s depois -> Expirou TTL, refaz a busca
    t2 = t0 + 65.0
    res3 = service.buscar_produtos_com_cache(tenant_id="t1", params={"tamanho": "38"}, now=t2)
    assert res3["sucesso"] is True

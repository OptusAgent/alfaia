"""
Testes de fechamento do WL_MODO=real (obter_produto, consultar_slots,
criar_agendamento) contra a wl-fake-api real, subida como subprocesso HTTP —
não como TestClient in-process, para exercitar o mesmo caminho de rede,
timeout e tradução que o modo mock não cobre.

Roda como subprocesso (não import direto) porque `wl-fake-api/app` e
`worker/app` são dois pacotes Python distintos chamados `app`; misturá-los
no mesmo processo de teste causaria colisão de namespace.
"""
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

from app.services.weblocacao_service import WebLocacaoService, WLException

WL_FAKE_API_ROOT = Path(__file__).resolve().parents[2] / "wl-fake-api"


def _porta_livre() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def wl_fake_api_url():
    porta = _porta_livre()
    base_url = f"http://127.0.0.1:{porta}"

    processo = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(porta), "--log-level", "warning"],
        cwd=str(WL_FAKE_API_ROOT),
    )
    try:
        for _ in range(50):
            try:
                if httpx.get(f"{base_url}/health", timeout=0.5).status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            time.sleep(0.2)
        else:
            processo.terminate()
            pytest.fail("wl-fake-api não subiu a tempo para os testes de real-mode.")

        yield base_url
    finally:
        processo.terminate()
        processo.wait(timeout=5)


@pytest.fixture
def service_real(wl_fake_api_url, monkeypatch):
    monkeypatch.setenv("WL_MODO", "real")
    monkeypatch.setenv("WL_BASE_URL", wl_fake_api_url)
    monkeypatch.setenv("WL_API_KEY", "chave_teste_real_mode")
    return WebLocacaoService()


def test_buscar_produtos_real_mode_traduz_sem_vazar_campos_erp(service_real):
    produtos = service_real.buscar_produtos(tenant_id="t1", categoria="casamento/noiva")
    assert len(produtos) > 0
    for p in produtos:
        assert hasattr(p, "valor_aluguel")
        assert hasattr(p, "ref")
        assert hasattr(p, "disponivel")


def test_obter_produto_real_mode(service_real):
    produtos = service_real.buscar_produtos(tenant_id="t1", categoria="casamento/traje-masculino")
    produto_id = produtos[0].id

    detalhe = service_real.obter_produto(produto_id, tenant_id="t1")
    assert detalhe.id == produto_id


def test_consultar_slots_real_mode(service_real):
    slots = service_real.consultar_slots(tenant_id="t1", tipo="prova", data_inicio="2026-09-10")
    assert len(slots) == 4
    assert all(s.vagas_totais == 2 for s in slots)


def test_criar_agendamento_real_mode_confirma_via_fake_erp(service_real):
    ag = service_real.criar_agendamento(
        tenant_id="t1",
        tipo="prova",
        data="2026-09-11",
        hora="09:00",
        cliente_nome="Lead Teste Real Mode",
        cliente_telefone="5585999998888",
    )
    assert ag.status == "confirmado"
    assert ag.id.startswith("wl_ag_")


def test_produto_inexistente_real_mode_gera_wlexception_4xx(service_real):
    with pytest.raises(WLException) as excinfo:
        service_real.obter_produto("nao_existe_123", tenant_id="t1")
    assert excinfo.value.status_code == 404

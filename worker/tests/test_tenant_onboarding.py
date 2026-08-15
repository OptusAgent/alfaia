import pytest
from app.services.tenant_onboarding_service import tenant_onboarding_service
from app.services.ia_config_service import ia_config_service
from app.services.weblocacao_service import weblocacao_service


def test_provisionar_tenant_transacional():
    """Testa o provisionamento transacional em 1 passo de um novo tenant e seus relacionamentos (AC 1, AC 2, AC 3, AC 4)."""
    nome_loja = "Ateliê Paris Viana"
    dono_email = "contato@parisviana.com.br"
    dono_nome = "Helena Viana"

    res = tenant_onboarding_service.provisionar_tenant_completo(
        nome_loja=nome_loja,
        dono_email=dono_email,
        dono_nome=dono_nome,
        canal_tipo="uazapi",
        wl_modo="mock",
    )

    assert res["sucesso"] is True
    tenant_id = res["tenant"]["id"]

    # 1. Valida criação do tenant e membro dono (AC 1)
    tenant_obj = tenant_onboarding_service.tenants[tenant_id]
    assert tenant_obj.nome == nome_loja

    membro_dono = next(m for m in tenant_onboarding_service.membros if m.tenant_id == tenant_id)
    assert membro_dono.email == dono_email
    assert membro_dono.papel == "dono"

    # 2. Valida conexão de canal (AC 2)
    canal = next(c for c in tenant_onboarding_service.canais if c.tenant_id == tenant_id)
    assert canal.tipo == "uazapi"

    # 3. Valida modo 'mock' da WebLocação (AC 3, I8)
    assert weblocacao_service.modos_tenant.get(tenant_id) == "mock"

    # 4. Valida criação da ia_config com valores padrão (AC 4)
    config = ia_config_service.obter_config(tenant_id=tenant_id)
    assert config["persona_nome"] == "Atendente da Alfaia"
    assert config["janela_retomada_dias"] == 7


def test_smoke_isolamento_tenant_novo():
    """Testa se o novo tenant possui 100% de isolamento de dados pós-onboarding (AC 5)."""
    res = tenant_onboarding_service.provisionar_tenant_completo(
        nome_loja="Loja Isolada Teste",
        dono_email="dono@isolada.com",
        dono_nome="Carlos Teste",
    )

    tenant_id = res["tenant"]["id"]
    smoke_res = tenant_onboarding_service.testar_isolamento_tenant(tenant_id=tenant_id)

    assert smoke_res["sucesso"] is True
    assert smoke_res["isolamento_confirmado"] is True

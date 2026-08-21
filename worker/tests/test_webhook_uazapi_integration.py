import json

import pytest

from app.adapters.base import PayloadNormalizado, ResultadoEnvio
from app.routers import webhooks


@pytest.mark.asyncio
async def test_webhook_resolves_channel_fetches_ia_config_and_sends_with_real_instance(monkeypatch):
    calls = {
        "canal_token": None,
        "ia_tenant": None,
        "registered": [],
        "adapter_init": None,
        "sent": None,
        "ia_config": None,
        "identity": None,
        "conversa": None,
        "history": None,
        "nome_atualizado": None,
    }

    class FakeSupabase:
        async def buscar_canal_por_token(self, token):
            calls["canal_token"] = token
            return {
                "id": "canal-123",
                "tenant_id": "tenant-123",
                "uazapi_base_url": "https://uazapi.alfaia.test",
                "uazapi_instancia": "loja-centro",
                "uazapi_token": "token-real-instancia",
            }

        async def buscar_ia_config(self, tenant_id):
            calls["ia_tenant"] = tenant_id
            return {
                "tenant_id": tenant_id,
                "modelo": "openai/gpt-4o-mini",
                "prompt_sistema": "Prompt do banco",
            }

        async def registrar_mensagem(self, payload):
            calls["registered"].append(payload)

        async def identificar_lead(self, tenant_id, telefone, push_name, origem="whatsapp_organico"):
            calls["identity"] = {
                "tenant_id": tenant_id,
                "telefone": telefone,
                "push_name": push_name,
                "origem": origem,
            }
            return {
                "contato_id": "contato-db-123",
                "lead_id": "lead-db-123",
                "entrada": "continuacao",
            }

        async def upsert_conversa(self, tenant_id, contato_id, lead_id, canal_id):
            calls["conversa"] = {
                "tenant_id": tenant_id,
                "contato_id": contato_id,
                "lead_id": lead_id,
                "canal_id": canal_id,
            }
            return {"id": "conversa-db-123"}

        async def buscar_historico_mensagens(self, conversa_id, limit=20):
            calls["history"] = {"conversa_id": conversa_id, "limit": limit}
            return [
                {
                    "id": "msg-hist-1",
                    "remetente": "lead",
                    "texto": "Oi",
                    "enviado_em": "2026-08-17T12:00:00+00:00",
                }
            ]

        async def atualizar_contato_nome(self, contato_id, nome):
            calls["nome_atualizado"] = {"contato_id": contato_id, "nome": nome}

        async def buscar_lead(self, lead_id):
            return None

        async def atualizar_status_lead(self, lead_id, status, status_alterado_por, status_alterado_em, motivo_descarte=None, followup_tentativas=None):
            calls["status_lead_atualizado"] = {"lead_id": lead_id, "status": status}

        async def registrar_lead_evento(self, **kwargs):
            calls.setdefault("lead_eventos", []).append(kwargs)

    class FakeAdapter:
        def __init__(self, base_url, instance_name, token, **kwargs):
            calls["adapter_init"] = {
                "base_url": base_url,
                "instance_name": instance_name,
                "token": token,
            }

        def normalizar_webhook(self, raw, headers):
            return [
                PayloadNormalizado(
                    tenant_id="fallback-tenant",
                    canal_id="fallback-canal",
                    provider="uazapi",
                    telefone="5585988124477",
                    push_name="Cliente",
                    mensagem="Oi, me chamo Mariana Silva e quero agendar uma prova",
                    wa_message_id="wamid.qa.webhook",
                    timestamp=1786900000,
                    data_atual="2026-08-17",
                )
            ]

        async def enviar_texto(self, to, text):
            calls["sent"] = {"to": to, "text": text}
            return ResultadoEnvio(sucesso=True, wa_message_id="wamid.qa.sent")

    class FakeAI:
        def processar_atendimento(self, **kwargs):
            calls["ia_config"] = kwargs["ia_config"]
            assert kwargs["tenant_id"] == "tenant-123"
            assert kwargs["lead_dto"].contato_id == "contato-db-123"
            assert kwargs["lead_dto"].id == "lead-db-123"
            assert kwargs["tipo_entrada"] == "continuacao"
            assert kwargs["historico_mensagens"][0]["texto"] == "Oi"
            return type(
                "AIResult",
                (),
                {"texto_resposta": "Resposta via OpenRouter mockada.", "midias_sugeridas": [], "contato_nome_atualizado": None},
            )()

    monkeypatch.setattr(webhooks, "supabase_rest_service", FakeSupabase())
    monkeypatch.setattr(webhooks, "UazapiAdapter", FakeAdapter)
    monkeypatch.setattr(webhooks, "ai_engine_service", FakeAI())

    raw = json.dumps(
        {
            "wa_message_id": "wamid.qa.webhook",
            "event": "message.received",
            "telefone": "85988124477",
            "mensagem": "Oi, me chamo Mariana Silva e quero agendar uma prova",
        }
    ).encode("utf-8")

    await webhooks._processar_payload_background(
        provider="uazapi",
        raw_body=raw,
        headers={},
        token="token-webhook",
    )

    assert calls["canal_token"] == "token-webhook"
    assert calls["ia_tenant"] == "tenant-123"
    assert calls["adapter_init"] == {
        "base_url": "https://uazapi.alfaia.test",
        "instance_name": "loja-centro",
        "token": "token-real-instancia",
    }
    assert calls["ia_config"]["prompt_sistema"] == "Prompt do banco"
    assert calls["identity"] == {
        "tenant_id": "tenant-123",
        "telefone": "5585988124477",
        "push_name": "Mariana Silva",
        "origem": "whatsapp_organico",
    }
    assert calls["nome_atualizado"] == {"contato_id": "contato-db-123", "nome": "Mariana Silva"}
    assert calls["conversa"] == {
        "tenant_id": "tenant-123",
        "contato_id": "contato-db-123",
        "lead_id": "lead-db-123",
        "canal_id": "canal-123",
    }
    assert calls["history"] == {"conversa_id": "conversa-db-123", "limit": 20}
    assert calls["sent"] == {
        "to": "5585988124477",
        "text": "Resposta via OpenRouter mockada.",
    }
    assert calls["registered"][0]["canal_id"] == "canal-123"
    assert calls["registered"][0]["conversa_id"] == "conversa-db-123"
    assert calls["registered"][0]["lead_id"] == "lead-db-123"
    assert calls["registered"][1]["status"] == "enviado"
    assert calls["registered"][1]["conversa_id"] == "conversa-db-123"


@pytest.mark.asyncio
async def test_webhook_persiste_mudanca_de_status_do_lead_no_postgres(monkeypatch):
    """
    Story 6.6, achado real em produção (2026-08-21): `webhooks.py` montava `LeadDTO` sempre com
    `status="qualificando"` fixo e nunca persistia de volta qualquer mudança feita pelo motor de
    IA (`mover_status`/`agendar` mutavam só o DTO da requisição). Este teste simula o motor real
    mutando `lead_dto.status` em memória (mesmo efeito que `status_transition_service` produz via
    `mover_status`/`agendar`) e confirma que o webhook lê o status REAL do lead antes de chamar a
    IA e grava a mudança de volta (status + evento) depois.
    """
    calls = {"lead_buscado": None, "status_atualizado": None, "eventos": []}

    class FakeSupabase:
        async def buscar_canal_por_token(self, token):
            return {
                "id": "canal-123", "tenant_id": "tenant-123",
                "uazapi_base_url": "https://uazapi.alfaia.test",
                "uazapi_instancia": "loja-centro", "uazapi_token": "token-real-instancia",
            }

        async def buscar_ia_config(self, tenant_id):
            return {"tenant_id": tenant_id, "modelo": "openai/gpt-4o-mini", "prompt_sistema": None}

        async def registrar_mensagem(self, payload):
            pass

        async def identificar_lead(self, tenant_id, telefone, push_name, origem="whatsapp_organico"):
            return {"contato_id": "contato-db-123", "lead_id": "lead-db-123", "entrada": "continuacao"}

        async def upsert_conversa(self, tenant_id, contato_id, lead_id, canal_id):
            return {"id": "conversa-db-123"}

        async def buscar_historico_mensagens(self, conversa_id, limit=20):
            return []

        async def atualizar_contato_nome(self, contato_id, nome):
            pass

        async def buscar_lead(self, lead_id):
            calls["lead_buscado"] = lead_id
            return {"id": lead_id, "status": "qualificando"}

        async def atualizar_status_lead(self, lead_id, status, status_alterado_por, status_alterado_em, motivo_descarte=None, followup_tentativas=None):
            calls["status_atualizado"] = {"lead_id": lead_id, "status": status, "status_alterado_por": status_alterado_por}

        async def registrar_lead_evento(self, **kwargs):
            calls["eventos"].append(kwargs)

    class FakeAdapter:
        def __init__(self, base_url, instance_name, token, **kwargs):
            pass

        def normalizar_webhook(self, raw, headers):
            return [
                PayloadNormalizado(
                    tenant_id="fallback-tenant", canal_id="fallback-canal", provider="uazapi",
                    telefone="5585988124477", push_name="Cliente",
                    mensagem="Confirmo a prova", wa_message_id="wamid.qa.status",
                    timestamp=1786900000, data_atual="2026-08-21",
                )
            ]

        async def enviar_texto(self, to, text):
            return ResultadoEnvio(sucesso=True, wa_message_id="wamid.texto")

    class FakeAI:
        def processar_atendimento(self, **kwargs):
            # Simula o efeito real de `mover_status`/`agendar` durante o tool-calling: o `lead_dto`
            # passado por referência é mutado em memória.
            kwargs["lead_dto"].status = "agendado"
            return type(
                "AIResult",
                (),
                {"texto_resposta": "Prova confirmada!", "midias_sugeridas": [], "contato_nome_atualizado": None},
            )()

    monkeypatch.setattr(webhooks, "supabase_rest_service", FakeSupabase())
    monkeypatch.setattr(webhooks, "UazapiAdapter", FakeAdapter)
    monkeypatch.setattr(webhooks, "ai_engine_service", FakeAI())

    raw = json.dumps({
        "wa_message_id": "wamid.qa.status", "event": "message.received",
        "telefone": "85988124477", "mensagem": "Confirmo a prova",
    }).encode("utf-8")

    await webhooks._processar_payload_background(
        provider="uazapi", raw_body=raw, headers={}, token="token-webhook",
    )

    assert calls["lead_buscado"] == "lead-db-123"
    assert calls["status_atualizado"] == {
        "lead_id": "lead-db-123", "status": "agendado", "status_alterado_por": "ia",
    }
    assert len(calls["eventos"]) == 1
    assert calls["eventos"][0]["de"] == "qualificando"
    assert calls["eventos"][0]["para"] == "agendado"


@pytest.mark.asyncio
async def test_webhook_classificador_move_status_sem_tool_call_explicita(monkeypatch):
    """
    Story 6.6, AC 2: o classificador determinístico move `novo` -> `qualificando` a partir do
    TEXTO da mensagem do lead, mesmo quando o motor de IA (aqui, um FakeAI que nunca mexe em
    `lead_dto.status`) não chamou nenhuma tool de status — a mesma classe de "modelo pula a tool"
    já vista com `atualizar_lead` não pode quebrar esta transição.
    """
    calls = {"status_atualizado": None, "eventos": []}

    class FakeSupabase:
        async def buscar_canal_por_token(self, token):
            return {
                "id": "canal-123", "tenant_id": "tenant-123",
                "uazapi_base_url": "https://uazapi.alfaia.test",
                "uazapi_instancia": "loja-centro", "uazapi_token": "token-real-instancia",
            }

        async def buscar_ia_config(self, tenant_id):
            return {"tenant_id": tenant_id, "modelo": "openai/gpt-4o-mini", "prompt_sistema": None}

        async def registrar_mensagem(self, payload):
            pass

        async def identificar_lead(self, tenant_id, telefone, push_name, origem="whatsapp_organico"):
            return {"contato_id": "contato-db-123", "lead_id": "lead-db-123", "entrada": "primeiro_contato"}

        async def upsert_conversa(self, tenant_id, contato_id, lead_id, canal_id):
            return {"id": "conversa-db-123"}

        async def buscar_historico_mensagens(self, conversa_id, limit=20):
            return []

        async def atualizar_contato_nome(self, contato_id, nome):
            pass

        async def buscar_lead(self, lead_id):
            return {"id": lead_id, "status": "novo"}

        async def atualizar_status_lead(self, lead_id, status, status_alterado_por, status_alterado_em, motivo_descarte=None, followup_tentativas=None):
            calls["status_atualizado"] = {"lead_id": lead_id, "status": status}

        async def registrar_lead_evento(self, **kwargs):
            calls["eventos"].append(kwargs)

    class FakeAdapter:
        def __init__(self, base_url, instance_name, token, **kwargs):
            pass

        def normalizar_webhook(self, raw, headers):
            return [
                PayloadNormalizado(
                    tenant_id="fallback-tenant", canal_id="fallback-canal", provider="uazapi",
                    telefone="5585988124477", push_name="Cliente",
                    mensagem="É um casamento e quero um terno azul marinho completo",
                    wa_message_id="wamid.qa.classificador",
                    timestamp=1786900000, data_atual="2026-08-21",
                )
            ]

        async def enviar_texto(self, to, text):
            return ResultadoEnvio(sucesso=True, wa_message_id="wamid.texto")

    class FakeAI:
        def processar_atendimento(self, **kwargs):
            # NUNCA mexe em kwargs["lead_dto"].status — simula o modelo não chamando mover_status.
            return type(
                "AIResult",
                (),
                {"texto_resposta": "Ótima escolha! Vamos ver as opções.", "midias_sugeridas": [], "contato_nome_atualizado": None},
            )()

    monkeypatch.setattr(webhooks, "supabase_rest_service", FakeSupabase())
    monkeypatch.setattr(webhooks, "UazapiAdapter", FakeAdapter)
    monkeypatch.setattr(webhooks, "ai_engine_service", FakeAI())

    raw = json.dumps({
        "wa_message_id": "wamid.qa.classificador", "event": "message.received",
        "telefone": "85988124477", "mensagem": "É um casamento e quero um terno azul marinho completo",
    }).encode("utf-8")

    await webhooks._processar_payload_background(
        provider="uazapi", raw_body=raw, headers={}, token="token-webhook",
    )

    assert calls["status_atualizado"] == {"lead_id": "lead-db-123", "status": "qualificando"}
    assert len(calls["eventos"]) == 1
    assert calls["eventos"][0]["de"] == "novo"
    assert calls["eventos"][0]["para"] == "qualificando"


@pytest.mark.asyncio
async def test_webhook_envia_midias_antes_do_texto_e_falha_parcial_nao_bloqueia(monkeypatch):
    """
    Story 4.9, AC 3, 4, 5: mídias sugeridas pela IA são enviadas antes do texto; falha ao enviar
    uma delas não impede o envio das demais nem do texto final.
    """
    calls = {"registered": [], "midias_enviadas": [], "texto_enviado": None}

    class FakeSupabase:
        async def buscar_canal_por_token(self, token):
            return {
                "id": "canal-123",
                "tenant_id": "tenant-123",
                "uazapi_base_url": "https://uazapi.alfaia.test",
                "uazapi_instancia": "loja-centro",
                "uazapi_token": "token-real-instancia",
            }

        async def buscar_ia_config(self, tenant_id):
            return {"tenant_id": tenant_id, "modelo": "openai/gpt-4o-mini", "prompt_sistema": None}

        async def registrar_mensagem(self, payload):
            calls["registered"].append(payload)

        async def identificar_lead(self, tenant_id, telefone, push_name, origem="whatsapp_organico"):
            return {"contato_id": "contato-db-123", "lead_id": "lead-db-123", "entrada": "continuacao"}

        async def upsert_conversa(self, tenant_id, contato_id, lead_id, canal_id):
            return {"id": "conversa-db-123"}

        async def buscar_historico_mensagens(self, conversa_id, limit=20):
            return []

        async def atualizar_contato_nome(self, contato_id, nome):
            pass

        async def buscar_lead(self, lead_id):
            return None

        async def atualizar_status_lead(self, lead_id, status, status_alterado_por, status_alterado_em, motivo_descarte=None, followup_tentativas=None):
            pass

        async def registrar_lead_evento(self, **kwargs):
            pass

    class FakeAdapter:
        def __init__(self, base_url, instance_name, token, **kwargs):
            pass

        def normalizar_webhook(self, raw, headers):
            return [
                PayloadNormalizado(
                    tenant_id="fallback-tenant",
                    canal_id="fallback-canal",
                    provider="uazapi",
                    telefone="5585988124477",
                    push_name="Cliente",
                    mensagem="Quero ver ternos",
                    wa_message_id="wamid.qa.midia",
                    timestamp=1786900000,
                    data_atual="2026-08-17",
                )
            ]

        async def enviar_texto(self, to, text):
            calls["texto_enviado"] = text
            return ResultadoEnvio(sucesso=True, wa_message_id="wamid.texto")

        async def enviar_midia(self, to, url, tipo, caption=None):
            calls["midias_enviadas"].append(url)
            if url == "https://x/falha.jpg":
                return ResultadoEnvio(sucesso=False, erro="HTTP 500")
            return ResultadoEnvio(sucesso=True, wa_message_id=f"wamid.midia.{len(calls['midias_enviadas'])}")

    class FakeAI:
        def processar_atendimento(self, **kwargs):
            midia_ok = type("Midia", (), {"url": "https://x/ok.jpg", "legenda": "Terno Azul — tamanho 48 — R$ 400.00"})()
            midia_falha = type("Midia", (), {"url": "https://x/falha.jpg", "legenda": "Terno Cinza — tamanho 50 — R$ 420.00"})()
            return type(
                "AIResult",
                (),
                {
                    "texto_resposta": "Gostou de algum desses modelos?",
                    "midias_sugeridas": [midia_ok, midia_falha],
                    "contato_nome_atualizado": None,
                },
            )()

    monkeypatch.setattr(webhooks, "supabase_rest_service", FakeSupabase())
    monkeypatch.setattr(webhooks, "UazapiAdapter", FakeAdapter)
    monkeypatch.setattr(webhooks, "ai_engine_service", FakeAI())

    raw = json.dumps(
        {
            "wa_message_id": "wamid.qa.midia",
            "event": "message.received",
            "telefone": "85988124477",
            "mensagem": "Quero ver ternos",
        }
    ).encode("utf-8")

    await webhooks._processar_payload_background(
        provider="uazapi",
        raw_body=raw,
        headers={},
        token="token-webhook",
    )

    assert calls["midias_enviadas"] == ["https://x/ok.jpg", "https://x/falha.jpg"]
    # Falha na 2a mídia não impede o texto final de ser enviado
    assert calls["texto_enviado"] == "Gostou de algum desses modelos?"
    # Só a mídia com sucesso é registrada no histórico
    midias_registradas = [r for r in calls["registered"] if r.get("midia_tipo") == "image"]
    assert len(midias_registradas) == 1
    assert midias_registradas[0]["midia_url"] == "https://x/ok.jpg"


def test_webhook_required_env_blocks_missing_secret(monkeypatch):
    monkeypatch.delenv("UAZAPI_ADMIN_TOKEN", raising=False)

    with pytest.raises(RuntimeError, match="UAZAPI_ADMIN_TOKEN"):
        webhooks._required_env("UAZAPI_ADMIN_TOKEN")

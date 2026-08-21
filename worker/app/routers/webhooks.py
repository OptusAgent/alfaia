import json
import logging
import re
from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, Request, BackgroundTasks, Header, status
from app.services.webhook_service import webhook_service

logger = logging.getLogger("alfaia.webhooks_router")

router = APIRouter(prefix="/webhook", tags=["webhooks"])


import os
from app.adapters.uazapi import UazapiAdapter
from app.services.ai_engine import ai_engine_service
from app.services.context_builder import ContatoDTO, LeadDTO
from app.services.supabase_rest import supabase_rest_service
from app.services.status_classifier_service import status_classifier_service
from app.services.status_transition_service import status_transition_service


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if value:
        return value

    raise RuntimeError(f"Variavel de ambiente obrigatoria ausente: {name}")


def _headers_para_captura(headers: dict[str, Any]) -> dict[str, Any]:
    sensiveis = ("authorization", "token", "apikey", "api-key", "cookie", "set-cookie", "x-api-key")
    return {
        key: "[redacted]" if key.lower() in sensiveis else value
        for key, value in headers.items()
    }


def _url_para_captura(url: str) -> str:
    return re.sub(r"(/webhook/(?:uazapi|meta)/)[^/?#]+", r"\1[redacted]", url)


def datetime_from_timestamp(timestamp: int | None) -> str:
    if timestamp:
        try:
            return datetime.fromtimestamp(int(timestamp), timezone.utc).isoformat()
        except (TypeError, ValueError, OSError):
            pass
    return datetime.now(timezone.utc).isoformat()


def _nome_generico(nome: str | None) -> bool:
    normalizado = " ".join(str(nome or "").strip().lower().split())
    return normalizado in ("", "cliente", "cliente whatsapp", "whatsapp", "sem nome")


def _extrair_nome_explicito(mensagem: str) -> str | None:
    texto = " ".join(str(mensagem or "").strip().split())
    match = re.search(
        r"\b(?:meu nome (?:é|e)|me chamo|sou)\s+([A-ZÀ-Ýa-zà-ÿ][A-ZÀ-Ýa-zà-ÿ'´`~-]*(?:\s+[A-ZÀ-Ýa-zà-ÿ][A-ZÀ-Ýa-zà-ÿ'´`~-]*){0,3})",
        texto,
        re.IGNORECASE,
    )
    if not match:
        return None

    nome = re.split(r"[,.;!?]|\s+(?:e|quero|preciso|gostaria|vou)\b", match.group(1).strip(), maxsplit=1, flags=re.IGNORECASE)[0]
    nome = " ".join(nome.split())
    primeiro = nome.split()[0].lower() if nome else ""
    termos_nao_nome = {
        "padrinho",
        "madrinha",
        "noiva",
        "noivo",
        "formando",
        "formanda",
        "convidado",
        "convidada",
        "cliente",
    }
    if len(nome) < 2 or _nome_generico(nome) or primeiro in termos_nao_nome:
        return None
    return nome


def _nome_preferencial(push_name: str | None, mensagem: str) -> str:
    nome_explicito = _extrair_nome_explicito(mensagem)
    if nome_explicito:
        return nome_explicito
    if not _nome_generico(push_name):
        return str(push_name).strip()
    return "Cliente WhatsApp"


async def _processar_payload_background(
    provider: str,
    raw_body: bytes,
    headers: dict[str, Any],
    token: str,
):
    """
    Processamento do webhook UAZAPI/Meta (PRD §14.4, §19.1).
    - Normaliza o payload UAZAPI.
    - Executa a IA (LLM Distill 70B / OpenRouter) respeitando as regras invioláveis.
    - Dispara a resposta em tempo real no WhatsApp via UazapiAdapter.
    """
    try:
        data = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        wa_message_id = data.get("wa_message_id") or data.get("id") or data.get("key", {}).get("id")

        if wa_message_id and not webhook_service.verificar_e_registrar_idempotencia(wa_message_id):
            # Mensagem duplicada — descarte silencioso conforme §21.2
            return

        logger.info(f"Processando webhook [{provider}]: wa_message_id={wa_message_id}")

        # 1. Resolve o canal real pelo token do webhook.
        canal = await supabase_rest_service.buscar_canal_por_token(token) if token else None
        if canal:
            logger.info(
                "Canal UAZAPI resolvido para webhook: canal_id=%s tenant_id=%s instancia=%s",
                canal.get("id"),
                canal.get("tenant_id"),
                canal.get("uazapi_instancia"),
            )
        else:
            logger.warning("Canal nao encontrado pelo token do webhook. Usando fallback de ambiente.")

        # 2. Normaliza o payload UAZAPI
        uazapi_base_url = canal.get("uazapi_base_url") if canal else _required_env("UAZAPI_BASE_URL")
        adapter_token = (canal.get("uazapi_token") if canal else None) or token
        if not adapter_token:
            adapter_token = _required_env("UAZAPI_ADMIN_TOKEN")

        adapter = UazapiAdapter(
            base_url=uazapi_base_url,
            instance_name=(canal.get("uazapi_instancia") if canal else None) or "default",
            token=adapter_token,
        )

        payloads = adapter.normalizar_webhook(raw_body, headers)
        if not payloads:
            logger.info(
                "Nenhum payload de mensagem valido para processar no webhook. diagnostico=%s",
                adapter.diagnosticar_webhook(raw_body),
            )
            return

        payload = payloads[0]
        if canal:
            payload = payload.model_copy(
                update={
                    "tenant_id": canal.get("tenant_id"),
                    "canal_id": canal.get("id"),
                }
            )

        telefone = payload.telefone
        mensagem_cliente = payload.mensagem
        push_name = _nome_preferencial(payload.push_name, mensagem_cliente)

        if not telefone or not mensagem_cliente:
            logger.info(
                "Webhook sem telefone ou texto de mensagem. Ignorando. phone_present=%s text_present=%s diagnostico=%s",
                bool(telefone),
                bool(mensagem_cliente),
                adapter.diagnosticar_webhook(raw_body),
            )
            return

        logger.info(f"Mensagem WhatsApp recebida de {push_name} ({telefone}): '{mensagem_cliente}'")

        identidade = await supabase_rest_service.identificar_lead(
            tenant_id=payload.tenant_id,
            telefone=telefone,
            push_name=push_name,
            origem="whatsapp_organico",
        )
        contato_id = identidade.get("contato_id") if identidade else None
        lead_id = identidade.get("lead_id") if identidade else None
        tipo_entrada = identidade.get("entrada") if identidade else "inbound_mensagem"
        if contato_id and not _nome_generico(push_name):
            await supabase_rest_service.atualizar_contato_nome(contato_id, push_name)

        conversa = None
        if contato_id:
            conversa = await supabase_rest_service.upsert_conversa(
                tenant_id=payload.tenant_id,
                contato_id=contato_id,
                lead_id=lead_id,
                canal_id=payload.canal_id,
            )
        conversa_id = conversa.get("id") if conversa else None

        await supabase_rest_service.registrar_mensagem(
            {
                "tenant_id": payload.tenant_id,
                "canal_id": payload.canal_id,
                "conversa_id": conversa_id,
                "lead_id": lead_id,
                "wa_message_id": payload.wa_message_id,
                "remetente": "lead",
                "texto": mensagem_cliente,
                "payload": data,
                "enviado_em": datetime_from_timestamp(payload.timestamp),
                "de_mim": False,
                "telefone": telefone,
                "conteudo": mensagem_cliente,
                "midia_url": payload.midia_url,
                "midia_tipo": payload.midia_tipo,
                "status": "recebido",
            }
        )

        ia_config = await supabase_rest_service.buscar_ia_config(payload.tenant_id)
        historico_mensagens = (
            await supabase_rest_service.buscar_historico_mensagens(conversa_id)
            if conversa_id
            else []
        )

        # 3. Executa a IA de Atendimento (AIEngine + LLM OpenRouter / DeepSeek)
        contato_dto = ContatoDTO(
            id=contato_id or f"contato_{telefone}",
            tenant_id=payload.tenant_id,
            telefone=telefone,
            nome=push_name,
            primeiro_contato_em=payload.data_atual,
        )

        # Hidrata o lead com o estado REAL do Postgres (story 6.6, achado real em produção,
        # 2026-08-21): até aqui, `LeadDTO` era sempre montado com `status="qualificando"` fixo,
        # ignorando o funil de verdade — um lead já `agendado`/`orcamento` voltava a ser tratado
        # como recém-qualificado a cada mensagem, e qualquer `mover_status` que a IA já chamava
        # não tinha efeito real (mutava só o DTO desta requisição). `lead_real=None` (lead novo,
        # acabou de ser criado por `identificar_lead` nesta mesma chamada) cai no default seguro.
        lead_real = await supabase_rest_service.buscar_lead(lead_id) if lead_id else None
        status_original = (lead_real or {}).get("status") or "novo"
        lead_dto = LeadDTO(
            id=lead_id or f"lead_{telefone}",
            tenant_id=payload.tenant_id,
            contato_id=contato_dto.id,
            status=status_original,
            origem="whatsapp_organico",
            evento_tipo=(lead_real or {}).get("evento_tipo"),
            evento_data=(lead_real or {}).get("evento_data"),
            peca_interesse=(lead_real or {}).get("peca_interesse"),
            tamanho=(lead_real or {}).get("tamanho"),
            cor=(lead_real or {}).get("cor"),
            valor_estimado=(lead_real or {}).get("valor_estimado"),
            followup_tentativas=(lead_real or {}).get("followup_tentativas") or 0,
            motivo_descarte=(lead_real or {}).get("motivo_descarte"),
            status_alterado_por=(lead_real or {}).get("status_alterado_por"),
            status_alterado_em=(lead_real or {}).get("status_alterado_em"),
        )

        res_ia = ai_engine_service.processar_atendimento(
            tenant_id=payload.tenant_id,
            contato_dto=contato_dto,
            lead_dto=lead_dto,
            tipo_entrada=tipo_entrada,
            mensagens_inbound=[mensagem_cliente],
            historico_mensagens=historico_mensagens,
            ia_config=ia_config,
        )

        texto_resposta = res_ia.texto_resposta
        logger.info(f"Resposta IA gerada para {telefone}: '{texto_resposta}'")

        # A IA confirmou/corrigiu o nome real do lead nesta troca (achado real em produção,
        # 2026-08-21: agendamento sem nome confiável de contato além do telefone) — persiste no
        # Postgres, mesmo caminho já usado para o push_name do WhatsApp.
        if res_ia.contato_nome_atualizado and contato_id:
            await supabase_rest_service.atualizar_contato_nome(contato_id, res_ia.contato_nome_atualizado)

        # Classificador determinístico de status (story 6.6, AC 2-4): NUNCA depende de o modelo
        # decidir chamar `mover_status` — lê o texto real da troca (mensagem do lead + resposta da
        # IA) e propõe uma transição sozinho. `status_transition_service` continua validando
        # (MV1-MV5): se `agendar`/`mover_status` já mudou o status para algo mais adiante no funil
        # nesta mesma troca, uma sugestão "para trás" do classificador é rejeitada automaticamente.
        zera_followup_tentativas = False
        if lead_id:
            status_destino, motivo_classificacao = status_classifier_service.classificar_transicao(
                status_atual=lead_dto.status,
                mensagens_lead=[mensagem_cliente],
                texto_resposta_ia=texto_resposta,
            )
            if status_destino:
                # story 6.7, AC 5: lead que estava em follow_up e respondeu — zera o contador de
                # tentativas do job de silêncio (worker/app/services/followup_worker_service.py),
                # senão ele carrega tentativas de um ciclo de silêncio já encerrado para o próximo.
                if lead_dto.status == "follow_up" and status_destino == "negociando":
                    zera_followup_tentativas = True
                sucesso_transicao, _ = status_transition_service.validar_e_mover_status(
                    tenant_id=payload.tenant_id,
                    lead=lead_dto,
                    status_destino=status_destino,
                    autor="ia",
                    motivo=motivo_classificacao,
                    lead_service=None,
                )
                if sucesso_transicao and zera_followup_tentativas:
                    lead_dto.followup_tentativas = 0

        # `mover_status`/`agendar` já podem ter mutado `lead_dto.status` em memória durante o
        # tool-calling (story 6.6) — persiste de volta no Postgres, senão a mudança nunca
        # sobrevive ao fim desta requisição (mesmo achado do gap acima).
        if lead_id and lead_dto.status != status_original:
            agora_iso = datetime.now(timezone.utc).isoformat()
            await supabase_rest_service.atualizar_status_lead(
                lead_id=lead_id,
                status=lead_dto.status,
                status_alterado_por="ia",
                status_alterado_em=agora_iso,
                motivo_descarte=lead_dto.motivo_descarte if lead_dto.status == "descartado" else None,
                followup_tentativas=0 if zera_followup_tentativas else None,
            )
            await supabase_rest_service.registrar_lead_evento(
                tenant_id=payload.tenant_id,
                lead_id=lead_id,
                tipo="status_alterado",
                autor="ia",
                de=status_original,
                para=lead_dto.status,
                motivo=lead_dto.motivo_descarte if lead_dto.status == "descartado" else None,
            )

        # 2.5. Envia as imagens reais dos produtos encontrados ANTES do texto (story 4.9, AC 1, 3)
        # — ordem natural de catálogo: mostrar a foto, depois perguntar/confirmar em texto. Falha
        # em uma mídia não bloqueia as demais nem o texto final (AC 5, é falha de canal, não de dado).
        for midia in res_ia.midias_sugeridas:
            try:
                res_midia = await adapter.enviar_midia(to=telefone, url=midia.url, tipo="image", caption=midia.legenda)
            except Exception as e:
                logger.warning(f"Falha ao enviar mídia de produto para {telefone}: {e}")
                continue

            if not res_midia.sucesso:
                logger.warning(f"Envio de mídia de produto falhou para {telefone}: {res_midia.erro}")
                continue

            await supabase_rest_service.registrar_mensagem(
                {
                    "tenant_id": payload.tenant_id,
                    "canal_id": payload.canal_id,
                    "conversa_id": conversa_id,
                    "lead_id": lead_id,
                    "wa_message_id": res_midia.wa_message_id,
                    "remetente": "ia",
                    "texto": midia.legenda,
                    "payload": {"provider": "uazapi", "res_envio": res_midia.model_dump()},
                    "enviado_em": datetime_from_timestamp(None),
                    "de_mim": True,
                    "telefone": telefone,
                    "conteudo": midia.legenda,
                    "midia_url": midia.url,
                    "midia_tipo": "image",
                    "status": "enviado",
                }
            )

        # 3. Dispara a resposta de volta no WhatsApp do cliente via UAZAPI (sem delay perceptível)
        if texto_resposta:
            res_envio = await adapter.enviar_texto(to=telefone, text=texto_resposta)
            logger.info(f"Resposta enviada via UAZAPI para {telefone}: wa_id={res_envio.wa_message_id}")
            await supabase_rest_service.registrar_mensagem(
                {
                    "tenant_id": payload.tenant_id,
                    "canal_id": payload.canal_id,
                    "conversa_id": conversa_id,
                    "lead_id": lead_id,
                    "wa_message_id": res_envio.wa_message_id,
                    "remetente": "ia",
                    "texto": texto_resposta,
                    "payload": {
                        "provider": "uazapi",
                        "res_envio": res_envio.model_dump(),
                    },
                    "enviado_em": datetime_from_timestamp(None),
                    "de_mim": True,
                    "telefone": telefone,
                    "conteudo": texto_resposta,
                    "midia_tipo": "text",
                    "status": "enviado" if res_envio.sucesso else "erro",
                }
            )

    except Exception as e:
        logger.error(f"Erro ao processar webhook em background: {e}", exc_info=True)



@router.post("/uazapi/{token}", status_code=status.HTTP_200_OK)
async def webhook_uazapi(
    token: str,
    request: Request,
):
    """
    Endpoint público de webhook para o canal UAZAPI (PRD §14.4 C2, AC 1-5).
    - Captura o payload cru imediatamente.
    - Processa dentro do request para manter CPU ativa no Cloud Run.
    """
    raw_body = await request.body()
    headers_dict = dict(request.headers)
    captura_url = _url_para_captura(str(request.url))
    captura_headers = _headers_para_captura(headers_dict)
    canal = await supabase_rest_service.buscar_canal_por_token(token) if token else None

    # 1. Captura bruta antes de qualquer processamento (AC 1)
    webhook_service.capturar_bruto(
        provider="uazapi",
        metodo=request.method,
        url=captura_url,
        headers=captura_headers,
        corpo=raw_body.decode("utf-8", errors="replace"),
        tenant_id=canal.get("tenant_id") if canal else None,
        hmac_ok=True,
    )
    await supabase_rest_service.registrar_webhook_captura(
        {
            "tenant_id": canal.get("tenant_id") if canal else None,
            "provider": "uazapi",
            "metodo": request.method,
            "url": captura_url,
            "headers": captura_headers,
            "corpo": raw_body.decode("utf-8", errors="replace"),
            "hmac_ok": True,
        }
    )

    # 2. Processa dentro do request: BackgroundTasks em Cloud Run pode ser interrompido
    # após o 200 quando a CPU volta a ser alocada sob demanda.
    await _processar_payload_background(
        provider="uazapi",
        raw_body=raw_body,
        headers=headers_dict,
        token=token,
    )

    # 3. Resposta 200 OK ao provider após tentativa de processamento.
    return {"status": "received", "provider": "uazapi"}


@router.post("/meta/{token}", status_code=status.HTTP_200_OK)
async def webhook_meta(
    token: str,
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str | None = Header(default=None),
):
    """
    Endpoint público de webhook para o canal Meta Cloud API (PRD §14.4 C1).
    """
    raw_body = await request.body()
    headers_dict = dict(request.headers)
    captura_url = _url_para_captura(str(request.url))
    captura_headers = _headers_para_captura(headers_dict)

    # Captura bruta
    webhook_service.capturar_bruto(
        provider="meta",
        metodo=request.method,
        url=captura_url,
        headers=captura_headers,
        corpo=raw_body.decode("utf-8", errors="replace"),
        tenant_id=None,
        hmac_ok=x_hub_signature_256 is not None,
    )
    await supabase_rest_service.registrar_webhook_captura(
        {
            "provider": "meta",
            "metodo": request.method,
            "url": captura_url,
            "headers": captura_headers,
            "corpo": raw_body.decode("utf-8", errors="replace"),
            "hmac_ok": x_hub_signature_256 is not None,
        }
    )

    background_tasks.add_task(
        _processar_payload_background,
        provider="meta",
        raw_body=raw_body,
        headers=headers_dict,
        token=token,
    )

    return {"status": "received", "provider": "meta"}

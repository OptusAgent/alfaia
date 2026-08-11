import json
import logging
from typing import Any
from fastapi import APIRouter, Request, BackgroundTasks, Header, Response, status
from app.services.webhook_service import webhook_service
from app.adapters.fake import FakeCanalAdapter

logger = logging.getLogger("alfaia.webhooks_router")

router = APIRouter(prefix="/webhook", tags=["webhooks"])


async def _processar_payload_background(
    provider: str,
    raw_body: bytes,
    headers: dict[str, Any],
    token: str,
):
    """
    Processamento em segundo plano acionado após a devolução imediata do 200 OK.
    """
    try:
        data = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        wa_message_id = data.get("wa_message_id") or data.get("id") or data.get("key", {}).get("id")

        if wa_message_id and not webhook_service.verificar_e_registrar_idempotencia(wa_message_id):
            # Mensagem duplicada — descarte silencioso conforme §21.2
            return

        logger.info(f"Processando webhook em background [{provider}]: wa_message_id={wa_message_id}")
    except Exception as e:
        logger.error(f"Erro ao processar webhook em background: {e}", exc_info=True)


@router.post("/uazapi/{token}", status_code=status.HTTP_200_OK)
async def webhook_uazapi(
    token: str,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Endpoint público de webhook para o canal UAZAPI (PRD §14.4 C2, AC 1-5).
    - Captura o payload cru imediatamente.
    - Devolve HTTP 200 OK sem aguardar o processamento downstream.
    """
    raw_body = await request.body()
    headers_dict = dict(request.headers)

    # 1. Captura bruta antes de qualquer processamento (AC 1)
    webhook_service.capturar_bruto(
        provider="uazapi",
        metodo=request.method,
        url=str(request.url),
        headers=headers_dict,
        corpo=raw_body.decode("utf-8", errors="replace"),
        tenant_id=None,
        hmac_ok=True,
    )

    # 2. Agenda processamento em segundo plano (AC 2)
    background_tasks.add_task(
        _processar_payload_background,
        provider="uazapi",
        raw_body=raw_body,
        headers=headers_dict,
        token=token,
    )

    # 3. Resposta imediata 200 OK ao provider (AC 2)
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

    # Captura bruta
    webhook_service.capturar_bruto(
        provider="meta",
        metodo=request.method,
        url=str(request.url),
        headers=headers_dict,
        corpo=raw_body.decode("utf-8", errors="replace"),
        tenant_id=None,
        hmac_ok=x_hub_signature_256 is not None,
    )

    background_tasks.add_task(
        _processar_payload_background,
        provider="meta",
        raw_body=raw_body,
        headers=headers_dict,
        token=token,
    )

    return {"status": "received", "provider": "meta"}

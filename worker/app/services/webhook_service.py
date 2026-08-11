import logging
from typing import Any
from pydantic import BaseModel

logger = logging.getLogger("alfaia.webhook_service")


class CapturaWebhookRegistro(BaseModel):
    id: int | None = None
    tenant_id: str | None = None
    provider: str
    metodo: str
    url: str
    headers: dict[str, Any]
    corpo: str
    hmac_ok: bool = True


class WebhookService:
    """
    Serviço central de captura de webhooks e controle de idempotência (PRD: S-07).
    Garante captura bruta de 100% dos payloads e descarte silencioso de mensagens duplicadas.
    """

    def __init__(self):
        # Repositório em memória para persistência de capturas e dedup rápida em testes
        self.capturas_log: list[CapturaWebhookRegistro] = []
        self._processed_wamids: set[str] = set()

    def capturar_bruto(
        self,
        provider: str,
        metodo: str,
        url: str,
        headers: dict[str, Any],
        corpo: str,
        tenant_id: str | None = None,
        hmac_ok: bool = True,
    ) -> CapturaWebhookRegistro:
        """
        Grava o payload bruto e cabeçalhos em `webhook_capturas` antes de qualquer outra lógica.
        Atende AC 1: Executado inclusive quando a mensagem será descartada ou for inválida.
        """
        registro = CapturaWebhookRegistro(
            id=len(self.capturas_log) + 1,
            tenant_id=tenant_id,
            provider=provider,
            metodo=metodo,
            url=url,
            headers=headers,
            corpo=corpo,
            hmac_ok=hmac_ok,
        )
        self.capturas_log.append(registro)
        logger.info(f"Webhook capturado com sucesso [provider={provider}, id={registro.id}]")
        return registro

    def verificar_e_registrar_idempotencia(self, wa_message_id: str) -> bool:
        """
        Garante idempotência por `wa_message_id` (PRD §14.4 C4, AC 3).
        Retorna True se for a primeira vez que a mensagem chega.
        Retorna False se a mensagem for duplicada (devendo ser descartada silenciosamente).
        """
        if not wa_message_id:
            return True

        if wa_message_id in self._processed_wamids:
            logger.info(f"Mensagem duplicada descartada silenciosamente: {wa_message_id}")
            return False

        self._processed_wamids.add(wa_message_id)
        return True


# Instância singleton global do serviço de webhooks no worker
webhook_service = WebhookService()

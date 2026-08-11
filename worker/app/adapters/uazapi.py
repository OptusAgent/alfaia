import json
import logging
import asyncio
import random
from typing import Any
import httpx
from app.adapters.base import CanalAdapter, Capabilities, PayloadNormalizado, ResultadoEnvio
from app.adapters.phone import normalizar_telefone

logger = logging.getLogger("alfaia.uazapi_adapter")


class UazapiAdapter:
    """
    Adapter para a API do UAZAPI (Canal WhatsApp não oficial / Web).
    Atende PRD §14.1, §14.2 e atende os critérios de aceite AC 1-6 da Story 2.3.
    """

    def __init__(
        self,
        base_url: str = "https://api.uazapi.com",
        instance_name: str = "default",
        token: str = "fake_token",
        delay_min_ms: int = 1000,
        delay_max_ms: int = 3000,
        httpx_client: httpx.AsyncClient | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.instance_name = instance_name
        self.token = token
        self.delay_min_ms = delay_min_ms
        self.delay_max_ms = delay_max_ms
        self._client = httpx_client

    @property
    def capabilities(self) -> Capabilities:
        return Capabilities(
            janela_24h=False,
            suporta_template=True,
            requer_delay=True,
            delay_min_ms=self.delay_min_ms,
            delay_max_ms=self.delay_max_ms,
            exige_horario_comercial=False,
        )

    def _get_headers(self, endpoint_type: str = "default") -> dict[str, str]:
        """
        Encapsula a inconsistência de headers documentada no PRD (§14.1):
        - `/send/text`: usa header `token`
        - `/message/sendMedia/{instance}`: usa header `apikey` ou `token`
        Nenhuma camada acima do adapter sabe dessa diferença.
        """
        if endpoint_type == "media":
            return {
                "Content-Type": "application/json",
                "apikey": self.token,
                "token": self.token,
            }
        return {
            "Content-Type": "application/json",
            "token": self.token,
        }

    def normalizar_webhook(self, raw: bytes, headers: dict[str, Any]) -> list[PayloadNormalizado]:
        """Converte JSON cru recebido no webhook do UAZAPI no contrato normalizado de §6.3."""
        if not raw:
            return []

        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            return []

        # Extração de campos do payload UAZAPI
        event = data.get("event") or data.get("type") or "message.received"
        if event not in ("message.received", "messages.upsert", "message"):
            # Apenas mensagens recebidas geram PayloadNormalizado
            return []

        msg_body = data.get("mensagem") or data.get("body") or data.get("text") or ""
        raw_phone = (
            data.get("telefone")
            or data.get("from")
            or data.get("data", {}).get("from")
            or ""
        )
        telefone = normalizar_telefone(raw_phone)
        push_name = data.get("push_name") or data.get("pushName") or "Cliente"
        wa_message_id = (
            data.get("wa_message_id")
            or data.get("id")
            or data.get("data", {}).get("id")
            or "wamid.unknown"
        )
        timestamp = data.get("timestamp") or 1754570000
        midia_url = data.get("midia_url") or data.get("mediaUrl")
        midia_tipo = data.get("midia_tipo") or data.get("mediaType") or ("image" if midia_url else "text")

        payload = PayloadNormalizado(
            tenant_id=data.get("tenant_id", "00000000-0000-0000-0000-000000000001"),
            canal_id=data.get("canal_id", "00000000-0000-0000-0000-000000000002"),
            provider="uazapi",
            telefone=telefone,
            push_name=push_name,
            mensagem=msg_body,
            midia_url=midia_url,
            midia_tipo=midia_tipo,
            wa_message_id=wa_message_id,
            timestamp=int(timestamp),
            data_atual=data.get("data_atual", "Sexta-feira, 7 de agosto de 2026, 14:32"),
        )
        return [payload]

    async def enviar_presence_composing(self, to: str) -> None:
        """Envia estado `presence: composing` para anti-ban (PRD §14.1, K1)."""
        clean_phone = normalizar_telefone(to)
        endpoint = f"{self.base_url}/chat/presence/{self.instance_name}"
        headers = self._get_headers()
        body = {"number": clean_phone, "presence": "composing"}

        try:
            if self._client:
                await self._client.post(endpoint, json=body, headers=headers)
            else:
                async with httpx.AsyncClient() as client:
                    await client.post(endpoint, json=body, headers=headers)
        except Exception as e:
            logger.warning(f"Falha ao enviar presence composing para UAZAPI: {e}")

    async def _aplicar_delay_anti_ban(self) -> None:
        """Aplica delay aleatório entre min e max ms para mitigação de banimento."""
        if self.delay_max_ms > 0:
            delay_sec = random.uniform(self.delay_min_ms, self.delay_max_ms) / 1000.0
            await asyncio.sleep(delay_sec)

    async def enviar_texto(self, to: str, text: str) -> ResultadoEnvio:
        clean_phone = normalizar_telefone(to)

        # Anti-ban: presence composing + delay
        await self.enviar_presence_composing(clean_phone)
        await self._aplicar_delay_anti_ban()

        endpoint = f"{self.base_url}/send/text"
        headers = self._get_headers("default")
        payload = {
            "instance": self.instance_name,
            "number": clean_phone,
            "text": text,
        }

        try:
            if self._client:
                res = await self._client.post(endpoint, json=payload, headers=headers)
            else:
                async with httpx.AsyncClient() as client:
                    res = await client.post(endpoint, json=payload, headers=headers)

            if res.status_code in (200, 201):
                res_data = res.json()
                wa_id = res_data.get("id") or res_data.get("wa_message_id") or f"uazapi_{clean_phone}"
                return ResultadoEnvio(sucesso=True, wa_message_id=wa_id)
            else:
                return ResultadoEnvio(sucesso=False, erro=f"HTTP {res.status_code}: {res.text}")
        except Exception as e:
            return ResultadoEnvio(sucesso=False, erro=str(e))

    async def enviar_midia(
        self, to: str, url: str, tipo: str, caption: str | None = None
    ) -> ResultadoEnvio:
        clean_phone = normalizar_telefone(to)
        await self.enviar_presence_composing(clean_phone)
        await self._aplicar_delay_anti_ban()

        endpoint = f"{self.base_url}/send/media"
        headers = self._get_headers("media")
        payload = {
            "instance": self.instance_name,
            "number": clean_phone,
            "mediaUrl": url,
            "mediaType": tipo,
            "caption": caption or "",
        }

        try:
            if self._client:
                res = await self._client.post(endpoint, json=payload, headers=headers)
            else:
                async with httpx.AsyncClient() as client:
                    res = await client.post(endpoint, json=payload, headers=headers)

            if res.status_code in (200, 201):
                res_data = res.json()
                wa_id = res_data.get("id") or res_data.get("wa_message_id") or f"uazapi_media_{clean_phone}"
                return ResultadoEnvio(sucesso=True, wa_message_id=wa_id)
            else:
                return ResultadoEnvio(sucesso=False, erro=f"HTTP {res.status_code}: {res.text}")
        except Exception as e:
            return ResultadoEnvio(sucesso=False, erro=str(e))

    async def enviar_template(
        self, to: str, nome: str, idioma: str, componentes: list[dict[str, Any]]
    ) -> ResultadoEnvio:
        # UAZAPI envia mensagens diretas; simula envio de template formatado
        texto_template = f"[{nome}]: {componentes}"
        return await self.enviar_texto(to, texto_template)

    async def marcar_lido(self, wa_message_id: str) -> None:
        endpoint = f"{self.base_url}/chat/markRead/{self.instance_name}"
        headers = self._get_headers()
        body = {"wa_message_id": wa_message_id}
        try:
            if self._client:
                await self._client.post(endpoint, json=body, headers=headers)
            else:
                async with httpx.AsyncClient() as client:
                    await client.post(endpoint, json=body, headers=headers)
        except Exception as e:
            logger.warning(f"Erro ao marcar lido na UAZAPI: {e}")

    # =========================================================================
    # MÉTODOS DE GESTÃO DE INSTÂNCIA & QR CODE (UAZAPI v2.1.0/2.1.1)
    # =========================================================================

    async def criar_instancia(self, name: str, admin_field01: str | None = None) -> dict[str, Any]:
        """
        Criação administrativa da instância na UAZAPI (POST /instance/create).
        """
        endpoint = f"{self.base_url}/instance/create"
        headers = self._get_headers()
        payload = {
            "name": name,
            "adminField01": admin_field01 or "",
        }

        if self._client:
            res = await self._client.post(endpoint, json=payload, headers=headers)
        else:
            async with httpx.AsyncClient() as client:
                res = await client.post(endpoint, json=payload, headers=headers)

        if res.status_code in (200, 201):
            return res.json()
        raise RuntimeError(f"Erro ao criar instância na UAZAPI: HTTP {res.status_code} - {res.text}")

    async def conectar_instancia(
        self,
        browser: str = "Chrome",
        system_name: str = "ALFAIA Portal",
        country: str = "BR",
    ) -> dict[str, Any]:
        """
        Inicia a sessão de pareamento e gera o QR Code na UAZAPI (POST /instance/connect).
        Retorna o dicionário contendo o QR Code (Base64/String) e o status inicial.
        """
        endpoint = f"{self.base_url}/instance/connect"
        headers = self._get_headers()
        payload = {
            "instanceName": self.instance_name,
            "browser": browser,
            "systemName": system_name,
            "proxy_managed_country": country,
        }

        if self._client:
            res = await self._client.post(endpoint, json=payload, headers=headers)
        else:
            async with httpx.AsyncClient() as client:
                res = await client.post(endpoint, json=payload, headers=headers)

        if res.status_code in (200, 201):
            return res.json()
        raise RuntimeError(f"Erro ao conectar/gerar QR Code na UAZAPI: HTTP {res.status_code} - {res.text}")

    async def configurar_webhook(self, instance_name: str, webhook_url: str) -> dict[str, Any]:
        """
        Configura/vincula a URL do webhook do ALFAIA na UAZAPI (POST /webhook/{instance_name}).
        """
        endpoint = f"{self.base_url}/webhook/{instance_name}"
        headers = self._get_headers()
        payload = {
            "url": webhook_url,
            "enabled": True,
        }

        if self._client:
            res = await self._client.post(endpoint, json=payload, headers=headers)
        else:
            async with httpx.AsyncClient() as client:
                res = await client.post(endpoint, json=payload, headers=headers)

        if res.status_code in (200, 201):
            return res.json()
        raise RuntimeError(f"Erro ao configurar webhook na UAZAPI: HTTP {res.status_code} - {res.text}")


# Assegura estritamente que UazapiAdapter satisfaz o Protocol CanalAdapter
_check_uazapi_protocol: CanalAdapter = UazapiAdapter()

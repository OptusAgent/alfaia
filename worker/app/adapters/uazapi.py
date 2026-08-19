import json
import logging
import asyncio
import random
import re
from datetime import datetime, timezone
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

    @staticmethod
    def _valor_verdadeiro(value: Any) -> bool:
        if value is True:
            return True
        if isinstance(value, str):
            return value.strip().lower() in ("true", "1", "yes", "sim")
        return value == 1

    @staticmethod
    def _iter_json_paths(value: Any, path: tuple[str, ...] = ()) -> list[tuple[tuple[str, ...], Any]]:
        items: list[tuple[tuple[str, ...], Any]] = []
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = (*path, str(key))
                items.append((child_path, child))
                items.extend(UazapiAdapter._iter_json_paths(child, child_path))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                child_path = (*path, str(index))
                items.append((child_path, child))
                items.extend(UazapiAdapter._iter_json_paths(child, child_path))
        return items

    @staticmethod
    def _path_label(path: tuple[str, ...]) -> str:
        return ".".join(path)

    @classmethod
    def _score_phone_candidate(cls, path: tuple[str, ...], value: Any) -> int:
        if not isinstance(value, str):
            return -1

        raw = value.strip()
        if not raw:
            return -1

        path_text = cls._path_label(path).lower()
        digits = normalizar_telefone(raw)
        has_whatsapp_jid = any(suffix in raw for suffix in ("@s.whatsapp.net", "@c.us"))
        is_group_jid = "@g.us" in raw

        if is_group_jid and not any(key in path_text for key in ("participant", "sender", "from")):
            return -1
        if not has_whatsapp_jid and not (10 <= len(digits) <= 14):
            return -1

        score = 1
        for key in ("participant", "remotejid", "sender", "from", "chatid", "jid", "phone", "number", "telefone"):
            if key in path_text:
                score += 3
        if has_whatsapp_jid:
            score += 5
        if 12 <= len(digits) <= 13:
            score += 2
        return score

    @classmethod
    def _score_text_candidate(cls, path: tuple[str, ...], value: Any) -> int:
        if not isinstance(value, str):
            return -1

        text = value.strip()
        if not text or len(text) > 4000:
            return -1
        if "@" in text and any(suffix in text for suffix in ("s.whatsapp.net", "c.us", "g.us")):
            return -1
        if text.startswith(("http://", "https://", "data:")):
            return -1
        if re.fullmatch(r"[\w.-]{18,}", text) and " " not in text:
            return -1

        path_text = cls._path_label(path).lower()
        score = -1
        for key in ("conversation", "text", "body", "caption", "mensagem", "message.text", "content"):
            if key in path_text:
                score = max(score, 3)
        if score < 0:
            return -1
        if any(ch.isspace() for ch in text) or len(text) <= 80:
            score += 1
        return score

    @classmethod
    def _best_candidate(cls, data: Any, scorer) -> str:
        best_score = -1
        best_value = ""
        for path, value in cls._iter_json_paths(data):
            score = scorer(path, value)
            if score > best_score:
                best_score = score
                best_value = value.strip() if isinstance(value, str) else str(value)
        return best_value if best_score >= 0 else ""

    @classmethod
    def diagnosticar_webhook(cls, raw: bytes) -> dict[str, Any]:
        """Retorna pistas estruturais do payload sem expor valores de cliente ou tokens."""
        try:
            data = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            return {"json_ok": False, "raw_size": len(raw or b"")}

        def keys_of(value: Any) -> list[str]:
            return list(value.keys())[:20] if isinstance(value, dict) else []

        phone_paths: list[str] = []
        text_paths: list[str] = []
        for path, value in cls._iter_json_paths(data):
            if len(phone_paths) < 8 and cls._score_phone_candidate(path, value) >= 0:
                phone_paths.append(cls._path_label(path))
            if len(text_paths) < 8 and cls._score_text_candidate(path, value) >= 0:
                text_paths.append(cls._path_label(path))

        data_node = data.get("data") or data.get("Data") or data.get("payload") or data.get("Payload")
        message_node = {}
        if isinstance(data_node, dict):
            message_node = data_node.get("message") or data_node.get("Message") or {}
        if not isinstance(message_node, dict):
            message_node = data.get("message") or data.get("Message") or {}

        return {
            "json_ok": True,
            "raw_size": len(raw or b""),
            "top_level_keys": keys_of(data),
            "data_keys": keys_of(data_node),
            "message_keys": keys_of(message_node),
            "phone_candidate_paths": phone_paths,
            "text_candidate_paths": text_paths,
        }

    def normalizar_webhook(self, raw: bytes, headers: dict[str, Any]) -> list[PayloadNormalizado]:
        """Converte JSON cru recebido no webhook do UAZAPI no contrato normalizado de §6.3."""
        if not raw:
            return []

        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            return []

        def first_value(*values: Any) -> Any:
            for value in values:
                if value not in (None, ""):
                    return value
            return ""

        def get_any(source: dict[str, Any], *keys: str) -> Any:
            if not isinstance(source, dict):
                return ""

            for key in keys:
                if key in source and source[key] not in (None, ""):
                    return source[key]

            lower_map = {str(k).lower(): v for k, v in source.items()}
            for key in keys:
                value = lower_map.get(key.lower())
                if value not in (None, ""):
                    return value

            return ""

        def nested(source: dict[str, Any], *path: str | int) -> Any:
            current: Any = source
            for key in path:
                if isinstance(current, list) and isinstance(key, int):
                    current = current[key] if len(current) > key else None
                    continue
                if not isinstance(current, dict):
                    return ""
                current = get_any(current, str(key))
            return current or ""

        data_node = first_value(
            get_any(data, "data", "Data", "payload", "Payload"),
            {},
        )
        if not isinstance(data_node, dict):
            data_node = {}

        message_node = first_value(
            get_any(data, "message", "Message"),
            get_any(data_node, "message", "Message"),
            nested(data_node, "messages", 0),
            nested(data_node, "Messages", 0),
        )
        if not isinstance(message_node, dict):
            message_node = {}

        key_node = first_value(
            get_any(data, "key", "Key"),
            get_any(data_node, "key", "Key"),
            get_any(message_node, "key", "Key"),
        )
        if not isinstance(key_node, dict):
            key_node = {}

        if self._valor_verdadeiro(first_value(
            get_any(data, "fromMe", "FromMe"),
            get_any(data, "wasSentByApi", "WasSentByApi"),
            get_any(data_node, "fromMe", "FromMe"),
            get_any(data_node, "wasSentByApi", "WasSentByApi"),
            get_any(key_node, "fromMe", "FromMe"),
        )):
            return []

        # Extração de campos do payload UAZAPI
        event = str(get_any(data, "event", "Event", "type", "Type", "eventType", "EventType") or "message.received").lower()
        if event not in ("message.received", "messages.upsert", "message", "messages"):
            # Apenas mensagens recebidas geram PayloadNormalizado
            return []

        msg_body = first_value(
            get_any(data, "mensagem", "body", "Body", "text", "Text", "conversation", "Conversation"),
            get_any(data_node, "mensagem", "body", "Body", "text", "Text", "conversation", "Conversation"),
            get_any(message_node, "conversation", "Conversation", "content", "Content", "text", "Text", "body", "Body"),
            nested(message_node, "extendedTextMessage", "text"),
            nested(message_node, "ExtendedTextMessage", "text"),
            nested(message_node, "imageMessage", "caption"),
            nested(message_node, "ImageMessage", "caption"),
            nested(message_node, "videoMessage", "caption"),
            nested(message_node, "VideoMessage", "caption"),
        )
        if not msg_body:
            msg_body = self._best_candidate(data, self._score_text_candidate)

        raw_phone = first_value(
            get_any(data, "telefone", "phone", "Phone", "number", "Number", "from", "From", "remoteJid", "RemoteJid"),
            get_any(data_node, "telefone", "phone", "Phone", "number", "Number", "from", "From", "remoteJid", "RemoteJid", "chatId", "ChatID", "jid", "Jid"),
            get_any(key_node, "remoteJid", "RemoteJid", "participant", "Participant"),
            get_any(message_node, "chatid", "chatId", "ChatID", "remoteJid", "RemoteJid", "from", "From", "sender", "Sender"),
            ""
        )
        if not raw_phone:
            raw_phone = self._best_candidate(data, self._score_phone_candidate)
        telefone = normalizar_telefone(raw_phone)
        push_name = first_value(
            get_any(data, "push_name", "pushName", "PushName", "senderName", "SenderName"),
            get_any(data_node, "push_name", "pushName", "PushName", "senderName", "SenderName"),
            get_any(message_node, "push_name", "pushName", "PushName", "senderName", "SenderName"),
            nested(data, "chat", "name"),
            nested(data, "Chat", "Name"),
            "Cliente",
        )
        wa_message_id = first_value(
            get_any(data, "wa_message_id", "messageid", "messageId", "MessageID", "id", "ID"),
            get_any(data_node, "messageid", "messageId", "MessageID", "id", "ID"),
            get_any(message_node, "messageid", "messageId", "MessageID", "id", "ID"),
            get_any(key_node, "id", "ID"),
            "wamid.unknown",
        )
        timestamp_bruto = first_value(
            get_any(data, "timestamp", "Timestamp", "messageTimestamp", "MessageTimestamp"),
            get_any(data_node, "timestamp", "Timestamp", "messageTimestamp", "MessageTimestamp"),
            get_any(message_node, "timestamp", "Timestamp", "messageTimestamp", "MessageTimestamp"),
        )
        agora_epoch = int(datetime.now(timezone.utc).timestamp())
        if str(timestamp_bruto).isdigit():
            timestamp_epoch = int(timestamp_bruto)
            # UAZAPI/Baileys envia messageTimestamp em milissegundos (13 digitos); normaliza para segundos.
            if timestamp_epoch > 10_000_000_000:
                timestamp_epoch //= 1000
        else:
            timestamp_epoch = agora_epoch
        midia_url = first_value(get_any(data, "midia_url", "mediaUrl", "MediaUrl"), get_any(data_node, "mediaUrl", "MediaUrl"))
        midia_tipo = first_value(get_any(data, "midia_tipo", "mediaType", "MediaType"), get_any(data_node, "mediaType", "MediaType"), "image" if midia_url else "text")
        if midia_tipo not in ("text", "audio", "image", "document"):
            midia_tipo = "text"

        payload = PayloadNormalizado(
            tenant_id=get_any(data, "tenant_id", "tenantId") or "00000000-0000-0000-0000-000000000001",
            canal_id=get_any(data, "canal_id", "canalId") or "00000000-0000-0000-0000-000000000002",
            provider="uazapi",
            telefone=telefone,
            push_name=push_name,
            mensagem=msg_body,
            midia_url=midia_url,
            midia_tipo=midia_tipo,
            wa_message_id=wa_message_id,
            timestamp=timestamp_epoch,
            data_atual=get_any(data, "data_atual", "dataAtual") or "Sexta-feira, 7 de agosto de 2026, 14:32",
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

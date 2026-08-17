import logging
import os
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import httpx

logger = logging.getLogger("alfaia.supabase_rest")


class SupabaseRestService:
    def __init__(
        self,
        url: str | None = None,
        service_key: str | None = None,
        httpx_client: httpx.AsyncClient | None = None,
    ):
        self.url = (url or os.getenv("SUPABASE_URL", "")).rstrip("/")
        self.service_key = (
            service_key
            or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            or os.getenv("SUPABASE_SERVICE_KEY")
            or ""
        )
        self._client = httpx_client

    @property
    def configurado(self) -> bool:
        return bool(self.url and self.service_key)

    def _headers(self, prefer: str | None = None) -> dict[str, str]:
        headers = {
            "apikey": self.service_key,
            "Authorization": f"Bearer {self.service_key}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        return headers

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response | None:
        if not self.configurado:
            logger.warning("Supabase REST nao configurado no worker.")
            return None

        endpoint = f"{self.url}/rest/v1/{path.lstrip('/')}"
        if self._client:
            return await self._client.request(method, endpoint, headers=self._headers(kwargs.pop("prefer", None)), **kwargs)

        async with httpx.AsyncClient(timeout=30) as client:
            return await client.request(method, endpoint, headers=self._headers(kwargs.pop("prefer", None)), **kwargs)

    async def buscar_canal_por_token(self, token: str) -> dict[str, Any] | None:
        token_q = quote(token, safe="")
        res = await self._request(
            "GET",
            f"canais?select=*&uazapi_token=eq.{token_q}&excluido_em=is.null&limit=1",
        )
        if not res or res.status_code >= 300:
            logger.error("Falha ao buscar canal por token: %s", res.text[:300] if res else "sem resposta")
            return None

        rows = res.json()
        return rows[0] if rows else None

    async def buscar_ia_config(self, tenant_id: str) -> dict[str, Any] | None:
        tenant_q = quote(tenant_id, safe="")
        res = await self._request("GET", f"ia_config?select=*&tenant_id=eq.{tenant_q}&limit=1")
        if not res or res.status_code >= 300:
            logger.error("Falha ao buscar ia_config: %s", res.text[:300] if res else "sem resposta")
            return None

        rows = res.json()
        return rows[0] if rows else None

    async def registrar_mensagem(self, payload: dict[str, Any]) -> None:
        res = await self._request(
            "POST",
            "mensagens",
            json=payload,
            prefer="resolution=ignore-duplicates",
        )
        if not res or res.status_code >= 300:
            logger.warning("Nao foi possivel registrar mensagem no Supabase: %s", res.text[:300] if res else "sem resposta")

    async def atualizar_status_canal(self, canal_id: str, status: str, raw: dict[str, Any] | None = None) -> None:
        res = await self._request(
            "PATCH",
            f"canais?id=eq.{quote(canal_id, safe='')}",
            json={
                "status": status,
                "ultimo_healthcheck_em": datetime.now(timezone.utc).isoformat(),
                "ultimo_status_raw": raw or {},
            },
        )
        if not res or res.status_code >= 300:
            logger.warning("Nao foi possivel atualizar status do canal: %s", res.text[:300] if res else "sem resposta")


supabase_rest_service = SupabaseRestService()

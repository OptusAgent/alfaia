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

    def _request_sync(self, method: str, path: str, **kwargs: Any) -> httpx.Response | None:
        """
        Variante síncrona de `_request`, para os serviços que ainda não são async
        (`WebLocacaoService`, `SchedulingService`, `AgendaSyncService` — ver Dev Notes
        da story 5.6). Sem client injetável: cada chamada abre e fecha seu próprio
        `httpx.Client`, mesmo padrão já usado em `weblocacao_service._chamar_api_real`.
        """
        if not self.configurado:
            logger.warning("Supabase REST nao configurado no worker (sync).")
            return None

        endpoint = f"{self.url}/rest/v1/{path.lstrip('/')}"
        with httpx.Client(timeout=30) as client:
            return client.request(method, endpoint, headers=self._headers(kwargs.pop("prefer", None)), **kwargs)

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

    async def identificar_lead(
        self,
        tenant_id: str,
        telefone: str,
        push_name: str | None,
        origem: str = "whatsapp_organico",
    ) -> dict[str, Any] | None:
        res = await self._request(
            "POST",
            "rpc/identificar_lead",
            json={
                "p_tenant": tenant_id,
                "p_telefone": telefone,
                "p_push_name": push_name or "Cliente WhatsApp",
                "p_origem": origem,
            },
        )
        if not res or res.status_code >= 300:
            logger.error("Falha ao identificar lead: %s", res.text[:300] if res else "sem resposta")
            return None

        data = res.json()
        if isinstance(data, list):
            return data[0] if data else None
        return data if isinstance(data, dict) else None

    async def upsert_conversa(
        self,
        tenant_id: str,
        contato_id: str,
        lead_id: str | None,
        canal_id: str | None,
    ) -> dict[str, Any] | None:
        res = await self._request(
            "POST",
            "conversas?on_conflict=tenant_id,contato_id",
            json={
                "tenant_id": tenant_id,
                "contato_id": contato_id,
                "lead_id": lead_id,
                "canal_id": canal_id,
                "estado": "ia",
                "ativada_em": datetime.now(timezone.utc).isoformat(),
            },
            prefer="resolution=merge-duplicates,return=representation",
        )
        if not res or res.status_code >= 300:
            logger.error("Falha ao criar/atualizar conversa: %s", res.text[:300] if res else "sem resposta")
            return None

        rows = res.json()
        return rows[0] if rows else None

    async def buscar_historico_mensagens(self, conversa_id: str, limit: int = 20) -> list[dict[str, Any]]:
        conversa_q = quote(conversa_id, safe="")
        res = await self._request(
            "GET",
            (
                "mensagens?select=id,remetente,texto,conteudo,de_mim,enviado_em,criado_em"
                f"&conversa_id=eq.{conversa_q}&order=enviado_em.asc&limit={limit}"
            ),
        )
        if not res or res.status_code >= 300:
            logger.warning("Nao foi possivel buscar historico da conversa: %s", res.text[:300] if res else "sem resposta")
            return []

        return res.json()

    async def atualizar_contato_nome(self, contato_id: str, nome: str) -> None:
        nome_limpo = " ".join(str(nome or "").split())
        if not contato_id or not nome_limpo:
            return

        res = await self._request(
            "PATCH",
            f"contatos?id=eq.{quote(contato_id, safe='')}",
            json={"nome": nome_limpo},
            prefer="return=minimal",
        )
        if not res or res.status_code >= 300:
            logger.warning("Nao foi possivel atualizar nome do contato: %s", res.text[:300] if res else "sem resposta")

    async def registrar_mensagem(self, payload: dict[str, Any]) -> None:
        res = await self._request(
            "POST",
            "rpc/registrar_mensagem_idempotente",
            json={"p_payload": payload},
        )
        if not res or res.status_code >= 300:
            logger.warning("Nao foi possivel registrar mensagem no Supabase: %s", res.text[:300] if res else "sem resposta")

    async def registrar_webhook_captura(self, payload: dict[str, Any]) -> None:
        res = await self._request(
            "POST",
            "webhook_capturas",
            json=payload,
            prefer="return=minimal",
        )
        if not res or res.status_code >= 300:
            logger.warning("Nao foi possivel registrar captura de webhook no Supabase: %s", res.text[:300] if res else "sem resposta")

    def registrar_wl_chamada(
        self,
        tenant_id: str,
        metodo: str,
        rota: str,
        status_code: int,
        latencia_ms: int,
        erro: str | None = None,
    ) -> None:
        """Grava telemetria de chamada ao WebLocação em wl_chamadas (I3, story 5.6, AC 1). Não bloqueante: nunca derruba o chamador."""
        try:
            res = self._request_sync(
                "POST",
                "wl_chamadas",
                json={
                    "tenant_id": tenant_id,
                    "metodo": metodo,
                    "rota": rota,
                    "status_code": status_code,
                    "latencia_ms": latencia_ms,
                    "erro": erro,
                },
                prefer="return=minimal",
            )
            if res is not None and res.status_code >= 300:
                logger.warning("Nao foi possivel registrar chamada WL em wl_chamadas: %s", res.text[:300])
        except Exception as e:
            logger.warning("Falha ao gravar wl_chamadas (nao bloqueante): %s", e)

    def buscar_agendamento_ativo(self, tenant_id: str, lead_id: str, data: str, hora: str) -> dict[str, Any] | None:
        """
        Consulta se já existe agendamento ativo para (tenant_id, lead_id, data, hora) — trava de
        idempotência I6 respaldada pelo índice `agendamentos_idempotencia` (story 5.6, AC 2).
        """
        try:
            res = self._request_sync(
                "GET",
                (
                    f"agendamentos?select=*&tenant_id=eq.{quote(tenant_id, safe='')}"
                    f"&lead_id=eq.{quote(lead_id, safe='')}&data=eq.{quote(data, safe='')}"
                    f"&hora=eq.{quote(hora, safe='')}&status=eq.ativo&limit=1"
                ),
            )
            if res is None or res.status_code >= 300:
                return None
            rows = res.json()
            return rows[0] if rows else None
        except Exception as e:
            logger.warning("Falha ao consultar agendamento ativo (nao bloqueante): %s", e)
            return None

    def inserir_agendamento(self, dados: dict[str, Any]) -> dict[str, Any] | None:
        """
        Insere um agendamento confirmado em `agendamentos` (story 5.6, AC 2). Um 409 aqui é o
        índice `agendamentos_idempotencia` ou `(tenant_id, wl_agendamento_id)` pegando uma corrida
        concorrente — trata como caminho idempotente, não como erro (I6).
        """
        try:
            res = self._request_sync("POST", "agendamentos", json=dados, prefer="return=representation")
            if res is None:
                return None
            if res.status_code == 409:
                logger.info("Insercao de agendamento colidiu com constraint de idempotencia (tratado como esperado).")
                return None
            if res.status_code >= 300:
                logger.warning("Falha ao inserir agendamento em agendamentos: %s", res.text[:300])
                return None
            rows = res.json()
            return rows[0] if rows else None
        except Exception as e:
            logger.warning("Falha ao gravar agendamentos (nao bloqueante): %s", e)
            return None

    def listar_agendamentos_periodo(
        self,
        tenant_id: str,
        data_inicio: str,
        data_fim: str,
        tipo: str | None = None,
        origem: str | None = None,
    ) -> list[dict[str, Any]] | None:
        """Lê agendamentos reais do Postgres por período (story 5.6, AC 5). None quando não configurado."""
        try:
            filtro = (
                f"agendamentos?select=*&tenant_id=eq.{quote(tenant_id, safe='')}"
                f"&data=gte.{quote(data_inicio, safe='')}&data=lte.{quote(data_fim, safe='')}"
                "&order=data.asc,hora.asc"
            )
            if tipo:
                filtro += f"&tipo=eq.{quote(tipo, safe='')}"
            if origem:
                filtro += f"&origem=eq.{quote(origem, safe='')}"

            res = self._request_sync("GET", filtro)
            if res is None or res.status_code >= 300:
                return None
            return res.json()
        except Exception as e:
            logger.warning("Falha ao listar agendamentos por periodo (nao bloqueante): %s", e)
            return None

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

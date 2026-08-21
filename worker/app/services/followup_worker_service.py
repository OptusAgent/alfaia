import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.context_builder import LeadDTO
from app.services.status_transition_service import _aware, status_transition_service
from app.services.supabase_rest import supabase_rest_service

logger = logging.getLogger("alfaia.followup_worker")

DEFAULT_JANELA_SILENCIO_HORAS = 24
DEFAULT_ORCAMENTO_FOLLOWUP_HORAS = 78
DEFAULT_MAX_TENTATIVAS = 3


class FollowupWorkerService:
    """
    Worker de Detecção de Silêncio e Automação de Follow-up real (PRD §10.2, §18.3, story 6.7).
    - `orcamento` tem janela própria (78h, `ia_config.orcamento_followup_horas`, decisão de
      produto desta sessão) — separada da janela geral de silêncio (24h,
      `ia_config.janela_silencio_horas`) que cobre `qualificando`/`negociando` (AC 1, 3, 6).
    - Nunca classifica silêncio como desistência: só move para `follow_up`, nunca direto para
      `descartado` (AC 1). O descarte por tentativas esgotadas é decisão explícita separada
      (`followup_expirar`, motivo `sem_resposta`), nunca implícito no silêncio em si.
    - `autor="sistema"` passa pela mesma trava MV3 (24h de proteção humana) que a IA — sem isso o
      job sobrescreveria uma movimentação humana recente, violando o AC 7 (achado desta story:
      antes da correção, `status_transition_service` só protegia `autor == "ia"`).
    """

    async def _obter_janelas(self, tenant_id: str) -> dict[str, int]:
        config = await supabase_rest_service.buscar_ia_config(tenant_id)
        return {
            "janela_silencio_horas": (config or {}).get("janela_silencio_horas") or DEFAULT_JANELA_SILENCIO_HORAS,
            "orcamento_followup_horas": (config or {}).get("orcamento_followup_horas") or DEFAULT_ORCAMENTO_FOLLOWUP_HORAS,
            "max_tentativas_followup": (config or {}).get("max_tentativas_followup") or DEFAULT_MAX_TENTATIVAS,
        }

    @staticmethod
    def _lead_dto_de_linha(row: dict[str, Any]) -> LeadDTO:
        return LeadDTO(
            id=row["id"],
            tenant_id=row["tenant_id"],
            contato_id=row["contato_id"],
            status=row["status"],
            followup_tentativas=row.get("followup_tentativas") or 0,
            status_alterado_por=row.get("status_alterado_por"),
            status_alterado_em=row.get("status_alterado_em"),
            ultimo_contato_em=row.get("ultimo_contato_em") or row.get("criado_em"),
            criado_em=row.get("criado_em"),
        )

    async def followup_scan(self, tenant_id: str = "tenant_piloto", now: datetime | None = None) -> dict[str, Any]:
        """
        Move para `follow_up` leads em `orcamento` (>= `orcamento_followup_horas`, default 78h) ou
        em `qualificando`/`negociando` (>= `janela_silencio_horas`, default 24h) sem nova mensagem
        (AC 1, 2, 3, 6). Lê `leads.ultimo_contato_em` real — atualizado pela RPC
        `identificar_lead` a cada mensagem inbound — nunca um relógio simulado em memória.
        """
        simulated_now = _aware(now or datetime.now(timezone.utc))
        janelas = await self._obter_janelas(tenant_id)

        linhas = await supabase_rest_service.listar_leads_para_followup(tenant_id)
        leads_processados = 0

        for row in linhas:
            if row["status"] not in ("orcamento", "qualificando", "negociando"):
                continue  # já está em follow_up — dedup natural, ver Dev Notes 6.7

            janela_horas = (
                janelas["orcamento_followup_horas"] if row["status"] == "orcamento" else janelas["janela_silencio_horas"]
            )
            lead_dto = self._lead_dto_de_linha(row)
            tempo_sem_resposta = simulated_now - _aware(lead_dto.ultimo_contato_em)
            if tempo_sem_resposta < timedelta(hours=janela_horas):
                continue

            status_anterior = lead_dto.status
            sucesso, _ = status_transition_service.validar_e_mover_status(
                tenant_id=tenant_id,
                lead=lead_dto,
                status_destino="follow_up",
                autor="sistema",
                motivo=f"Sem resposta há {janela_horas}h",
                now=simulated_now,
            )
            if not sucesso:
                continue  # MV3 (humano recente) ou outra regra bloqueou — não é erro, é a regra funcionando (AC 7)

            nova_tentativa = lead_dto.followup_tentativas + 1
            agora_iso = simulated_now.isoformat()
            await supabase_rest_service.atualizar_status_lead(
                lead_id=lead_dto.id,
                status="follow_up",
                status_alterado_por="sistema",
                status_alterado_em=agora_iso,
                followup_tentativas=nova_tentativa,
            )
            await supabase_rest_service.registrar_lead_evento(
                tenant_id=tenant_id,
                lead_id=lead_dto.id,
                tipo="followup_enviado",
                autor="sistema",
                de=status_anterior,
                para="follow_up",
                motivo=f"Silêncio de {janela_horas}h em '{status_anterior}'",
                detalhe={"tentativa": nova_tentativa},
            )
            leads_processados += 1

        logger.info(f"followup_scan executado com sucesso [tenant={tenant_id}, novos_followup={leads_processados}]")
        return {"sucesso": True, "leads_em_followup": leads_processados}

    async def followup_expirar(self, tenant_id: str = "tenant_piloto", now: datetime | None = None) -> dict[str, Any]:
        """Descarta automaticamente (motivo `sem_resposta`) leads em `follow_up` com tentativas
        esgotadas (>= `max_tentativas_followup`). Decisão explícita de descarte, distinta do
        silêncio em si (AC 1, 4)."""
        simulated_now = _aware(now or datetime.now(timezone.utc))
        janelas = await self._obter_janelas(tenant_id)
        max_tentativas = janelas["max_tentativas_followup"]

        linhas = await supabase_rest_service.listar_leads_para_followup(tenant_id)
        leads_descartados = 0

        for row in linhas:
            if row["status"] != "follow_up" or (row.get("followup_tentativas") or 0) < max_tentativas:
                continue

            lead_dto = self._lead_dto_de_linha(row)
            sucesso, _ = status_transition_service.validar_e_mover_status(
                tenant_id=tenant_id,
                lead=lead_dto,
                status_destino="descartado",
                autor="sistema",
                motivo="sem_resposta",
                now=simulated_now,
            )
            if not sucesso:
                continue

            await supabase_rest_service.atualizar_status_lead(
                lead_id=lead_dto.id,
                status="descartado",
                status_alterado_por="sistema",
                status_alterado_em=simulated_now.isoformat(),
                motivo_descarte="sem_resposta",
            )
            await supabase_rest_service.registrar_lead_evento(
                tenant_id=tenant_id,
                lead_id=lead_dto.id,
                tipo="descartado",
                autor="sistema",
                de="follow_up",
                para="descartado",
                motivo="sem_resposta",
            )
            leads_descartados += 1

        logger.info(f"followup_expirar executado com sucesso [tenant={tenant_id}, leads_descartados={leads_descartados}]")
        return {"sucesso": True, "leads_descartados": leads_descartados}

    async def loop_worker_followup(
        self,
        tenants: list[str],
        intervalo_scan_segundos: float = 900.0,
        ciclos_por_expirar: int = 4,
    ) -> None:
        """
        Job de plano de fundo portátil em asyncio (AC 5, wired via FastAPI lifespan em `main.py`)
        — nunca amarrado a Cloud Scheduler/Cloud Tasks, roda igual em Cloud Run e VPS
        (`.claude/rules/alfaia-stack-deploy.md`). Scan a cada 15 min; expiração a cada 4 scans
        (~1h), mesma cadência do desenho original.
        """
        contador_loops = 0
        while True:
            for tenant_id in tenants:
                try:
                    await self.followup_scan(tenant_id)
                    if contador_loops % ciclos_por_expirar == 0:
                        await self.followup_expirar(tenant_id)
                except Exception as e:
                    logger.error(f"Erro no loop do Followup Worker [tenant={tenant_id}]: {e}")
            contador_loops += 1
            await asyncio.sleep(intervalo_scan_segundos)


followup_worker_service = FollowupWorkerService()

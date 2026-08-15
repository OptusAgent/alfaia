import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from app.services.lead_service import lead_service, LeadModel, LeadEventoModel
from app.services.status_transition_service import status_transition_service

logger = logging.getLogger("alfaia.followup_worker")


class FollowupWorkerService:
    """
    Worker de Detecção de Silêncio e Automação de Follow-up (PRD §10.2, §18.3, AC 1-5).
    - Scans de 15 min (`followup_scan`) e 1 hora (`followup_expirar`) (AC 5).
    - Trava de silêncio: move para 'follow_up' após 24h sem resposta (AC 10.1).
    - Zeragem de contador ao lead responder (AC 10.3).
    - Descarte automático após max_tentativas (3) com motivo 'sem_resposta' sem nunca classificar silêncio como desistência (AC 4, AC 9.11).
    """

    def __init__(self):
        self._is_running = False
        # Configurações padrão do tenant (PRD §10.2, Task 4)
        self.configs: dict[str, dict[str, Any]] = {
            "tenant_piloto": {
                "janela_silencio_horas": 24,
                "max_tentativas": 3,
                "intervalo_tentativas_horas": 48,
                "disparo_automatico": False,
            }
        }

    def obter_config(self, tenant_id: str) -> dict[str, Any]:
        return self.configs.get(
            tenant_id,
            {
                "janela_silencio_horas": 24,
                "max_tentativas": 3,
                "intervalo_tentativas_horas": 48,
                "disparo_automatico": False,
            },
        )

    def followup_scan(self, tenant_id: str = "tenant_piloto", now: datetime | None = None) -> dict[str, Any]:
        """
        Executado a cada 15 min: Identifica leads sem resposta há >= janela_silencio_horas (24h) e os move para 'follow_up' (AC 1, AC 10.1).
        """
        simulated_now = now or datetime.now()
        config = self.obter_config(tenant_id)
        janela_horas = config["janela_silencio_horas"]

        leads_processados = 0
        for lead in lead_service.leads:
            if lead.tenant_id != tenant_id:
                continue

            if lead.status in ("orcamento", "qualificando", "negociando"):
                tempo_sem_resposta = simulated_now - lead.ultimo_contato_em
                if tempo_sem_resposta >= timedelta(hours=janela_horas):
                    status_anterior = lead.status
                    sucesso, _ = status_transition_service.validar_e_mover_status(
                        tenant_id=tenant_id,
                        lead=lead,
                        status_destino="follow_up",
                        autor="sistema",
                        now=simulated_now,
                    )
                    if sucesso:
                        lead.followup_tentativas += 1
                        lead_service.eventos.append(
                            LeadEventoModel(
                                id=len(lead_service.eventos) + 1,
                                tenant_id=tenant_id,
                                lead_id=lead.id,
                                tipo="followup_enviado",
                                de=status_anterior,
                                para="follow_up",
                                autor="sistema",
                                detalhe={"tentativa": lead.followup_tentativas, "mensagem": "Follow-up preparado por silêncio (24h)."},
                                criado_em=simulated_now,
                            )
                        )
                        leads_processados += 1

        logger.info(f"followup_scan executado com sucesso [novos_followup={leads_processados}]")
        return {"sucesso": True, "leads_em_followup": leads_processados}

    def followup_expirar(self, tenant_id: str = "tenant_piloto", now: datetime | None = None) -> dict[str, Any]:
        """
        Executado a cada 1 hora: Identifica leads em 'follow_up' com tentativas esgotadas (>= 3) e descarte automático com motivo 'sem_resposta' (AC 3, AC 4).
        """
        simulated_now = now or datetime.now()
        config = self.obter_config(tenant_id)
        max_tentativas = config["max_tentativas"]

        leads_descartados = 0
        for lead in lead_service.leads:
            if lead.tenant_id != tenant_id:
                continue

            if lead.status == "follow_up" and lead.followup_tentativas >= max_tentativas:
                sucesso, _ = status_transition_service.validar_e_mover_status(
                    tenant_id=tenant_id,
                    lead=lead,
                    status_destino="descartado",
                    autor="sistema",
                    motivo="sem_resposta",  # Motivo explícito de tentativas esgotadas (AC 4)
                    now=simulated_now,
                )
                if sucesso:
                    lead_service.eventos.append(
                        LeadEventoModel(
                            id=len(lead_service.eventos) + 1,
                            tenant_id=tenant_id,
                            lead_id=lead.id,
                            tipo="descartado",
                            de="follow_up",
                            para="descartado",
                            autor="sistema",
                            motivo="sem_resposta",
                            criado_em=simulated_now,
                        )
                    )
                    leads_descartados += 1

        logger.info(f"followup_expirar executado com sucesso [leads_descartados={leads_descartados}]")
        return {"sucesso": True, "leads_descartados": leads_descartados}

    def zerar_contador_ao_responder(self, lead_id: str, tenant_id: str = "tenant_piloto", now: datetime | None = None) -> bool:
        """
        Quando o lead responde, zera o contador de tentativas e o devolve para 'negociando' se estava em 'follow_up' (AC 2, AC 10.3).
        """
        simulated_now = now or datetime.now()
        lead = next((l for l in lead_service.leads if l.id == lead_id and l.tenant_id == tenant_id), None)
        if not lead:
            return False

        lead.followup_tentativas = 0
        lead.ultimo_contato_em = simulated_now

        if lead.status == "follow_up":
            # Devolve para 'negociando' (MV2 permite transição follow_up -> negociando)
            status_transition_service.validar_e_mover_status(
                tenant_id=tenant_id,
                lead=lead,
                status_destino="negociando",
                autor="ia",
                now=simulated_now,
            )
            logger.info(f"Lead respondeu: contador zerado e retornado para 'negociando' [lead_id={lead_id}]")

        return True

    async def loop_worker_followup(self, intervalo_scan_segundos: float = 900.0, intervalo_expirar_segundos: float = 3600.0):
        """
        Job de plano de fundo portátil em asyncio (AC 5, Task 5).
        """
        self._is_running = True
        logger.info("Follow-up Background Worker iniciado.")
        contador_loops = 0

        while self._is_running:
            try:
                self.followup_scan()
                if contador_loops % 4 == 0:  # A cada 4 scans de 15 min = 1 hora
                    self.followup_expirar()
                contador_loops += 1
            except Exception as e:
                logger.error(f"Erro no loop do Followup Worker: {e}")
            await asyncio.sleep(intervalo_scan_segundos)

    def parar_worker(self):
        self._is_running = False


followup_worker_service = FollowupWorkerService()

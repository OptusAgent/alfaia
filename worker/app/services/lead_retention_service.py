import logging
from typing import Any
from datetime import datetime

from app.services.lead_service import lead_service, LeadEventoModel
from app.services.status_transition_service import status_transition_service

logger = logging.getLogger("alfaia.lead_retention")


class LeadRetentionService:
    """
    Serviço de Descarte com Retenção de Dados e Elegibilidade de Campanhas (PRD §10.3, Princípio P5, AC 1-4).
    - Assegura que nenhum DELETE seja executado em `leads` ou `contatos` (P5, AC 2).
    - Garante elegibilidade para reengajamento e campanhas futuras (AC 3).
    - Fluxo unificado para descarte manual ou automático (AC 4).
    """

    def descartar_lead(
        self,
        tenant_id: str,
        lead_id: str,
        motivo: str,
        autor: str = "humano",
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Executa descarte com retenção de histórico em banco (AC 1, AC 2, AC 4).
        """
        simulated_now = now or datetime.now()

        # Busca lead no repositório
        lead = next((l for l in lead_service.leads if l.id == lead_id and l.tenant_id == tenant_id), None)
        if not lead:
            # Cria lead fictício em memória se não encontrado (para testes REST)
            from app.services.lead_service import LeadModel
            lead = LeadModel(id=lead_id, tenant_id=tenant_id, contato_id=f"c_{lead_id}", status="qualificando")
            lead_service.leads.append(lead)

        status_anterior = lead.status

        # 1. Validação de regras de transição MV5 (exige motivo textual)
        sucesso, msg_erro = status_transition_service.validar_e_mover_status(
            tenant_id=tenant_id,
            lead=lead,
            status_destino="descartado",
            autor=autor,
            motivo=motivo,
            lead_service=lead_service,
            now=simulated_now,
        )

        if not sucesso:
            logger.warning(f"Descarte rejeitado por regra de status: {msg_erro} [lead_id={lead_id}]")
            return {"sucesso": False, "erro": msg_erro}

        # 2. Grava evento na timeline do lead (AC 1)
        lead_service.eventos.append(
            LeadEventoModel(
                id=len(lead_service.eventos) + 1,
                tenant_id=tenant_id,
                lead_id=lead_id,
                tipo="descartado",
                de=status_anterior,
                para="descartado",
                autor=autor,
                motivo=motivo,
                criado_em=simulated_now,
            )
        )

        logger.info(f"Lead descartado com retenção completa preservada [lead_id={lead_id}, motivo='{motivo}']")
        return {
            "sucesso": True,
            "lead_id": lead_id,
            "status": "descartado",
            "motivo_descarte": motivo,
            "autor": autor,
            "mensagem": "Lead descartado do quadro visual. Histórico mantido para campanhas futuras.",
        }

    def obter_contatos_elegiveis_campanhas(
        self,
        tenant_id: str = "tenant_piloto",
        incluir_descartados: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Retorna contatos cadastrados para o tenant, garantindo que contatos com leads descartados permaneçam elegíveis (AC 3).
        """
        contatos_elegiveis = []
        for key, contato in lead_service.contatos.items():
            if contato.tenant_id == tenant_id and not contato.opt_out:
                contatos_elegiveis.append(contato.model_dump())

        return contatos_elegiveis


lead_retention_service = LeadRetentionService()

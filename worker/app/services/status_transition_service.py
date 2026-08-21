import logging
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger("alfaia.status_transition")

STATUS_ORDER = {
    "novo": 1,
    "qualificando": 2,
    "orcamento": 3,
    "follow_up": 4,
    "negociando": 5,
    "agendado": 6,
    "ganho": 7,
    "descartado": 99,
}

EXPLICIT_DESISTENCE_TERMS = [
    "já aluguei em outro lugar",
    "ja aluguei em outro lugar",
    "desisti",
    "não vou mais",
    "nao vou mais",
    "achei mais barato em outro lugar",
    "evento foi cancelado",
    "não tenho interesse",
    "nao tenho interesse",
    "para de me mandar mensagem",
]


class StatusTransitionService:
    """
    Serviço de Validação Server-side de Transição de Status e Aplicação das Regras MV1–MV6 (PRD §9.7, §9.8).
    """

    @staticmethod
    def classificar_desistencia(texto_mensagem: str | None) -> bool:
        """Classifica se o texto da mensagem contém desistência explícita (PRD §9.8). Silêncio nunca é desistência."""
        if not texto_mensagem:
            return False
        txt = texto_mensagem.lower().strip()
        return any(term in txt for term in EXPLICIT_DESISTENCE_TERMS)

    @staticmethod
    def validar_e_mover_status(
        tenant_id: str,
        lead: Any,
        status_destino: str,
        autor: str = "ia",
        motivo: str | None = None,
        lead_service: Any = None,
        now: datetime | None = None,
    ) -> tuple[bool, str]:
        simulated_now = now or datetime.now()
        status_atual = lead.status

        # 1. MV1: A IA nunca move para ganho. Apenas o humano marca contrato fechado (PRD §9.7, AC 2, T10)
        if autor == "ia" and status_destino == "ganho":
            msg_erro = "MV1: A IA é proibida de mover o status para 'ganho'. Apenas operadores humanos podem confirmar o fechamento do contrato."
            logger.warning(f"[REJEITADO MV1] {msg_erro} [lead_id={lead.id}]")
            return False, msg_erro

        # 2. MV3: Se humano moveu nas últimas 24h, a IA não sobrescreve — registra divergência (PRD §9.7, AC 4, T11)
        status_alterado_por = getattr(lead, "status_alterado_por", None) or "sistema"
        status_alterado_em = getattr(lead, "status_alterado_em", None) or lead.criado_em
        if autor == "ia" and status_alterado_por in ("atendente", "humano"):
            if (simulated_now - status_alterado_em) < timedelta(hours=24):
                msg_erro = "MV3: Alteração bloqueada. Um atendente humano movimentou este lead nas últimas 24h."
                logger.warning(f"[REJEITADO MV3] {msg_erro} [lead_id={lead.id}, status_humano={status_atual}]")
                if lead_service:
                    from app.services.lead_service import LeadEventoModel
                    lead_service.eventos.append(
                        LeadEventoModel(
                            id=len(lead_service.eventos) + 1,
                            tenant_id=tenant_id,
                            lead_id=lead.id,
                            tipo="divergencia_humano",
                            autor="sistema",
                            detalhe={
                                "tentativa_ia": status_destino,
                                "status_mantido": status_atual,
                                "motivo": "Movimentação humana protegida (janela 24h)",
                            },
                        )
                    )
                return False, msg_erro

        # 3. MV2: A IA nunca move para trás, exceto 'follow_up -> negociando' (PRD §9.7, AC 3)
        if autor == "ia" and status_destino != "descartado":
            ordem_atual = STATUS_ORDER.get(status_atual, 0)
            ordem_destino = STATUS_ORDER.get(status_destino, 0)
            if ordem_destino < ordem_atual:
                if not (status_atual == "follow_up" and status_destino == "negociando"):
                    msg_erro = f"MV2: A IA não pode mover status para trás no funil ({status_atual} -> {status_destino})."
                    logger.warning(f"[REJEITADO MV2] {msg_erro} [lead_id={lead.id}]")
                    return False, msg_erro

        # 4. MV5: Descarte por desistência exige motivo textual (PRD §9.7, AC 5)
        if status_destino == "descartado" and not motivo:
            msg_erro = "MV5: Movimentação para 'descartado' exige motivo textual descritivo."
            logger.warning(f"[REJEITADO MV5] {msg_erro} [lead_id={lead.id}]")
            return False, msg_erro

        # Transição autorizada com sucesso!
        lead.status = status_destino
        lead.status_alterado_em = simulated_now
        lead.status_alterado_por = autor
        if status_destino == "descartado":
            lead.motivo_descarte = motivo

        if lead_service:
            from app.services.lead_service import LeadEventoModel
            lead_service.eventos.append(
                LeadEventoModel(
                    id=len(lead_service.eventos) + 1,
                    tenant_id=tenant_id,
                    lead_id=lead.id,
                    tipo="status_alterado",
                    autor=autor,
                    detalhe={"de": status_atual, "para": status_destino, "motivo": motivo},
                )
            )

        logger.info(f"Status alterado com sucesso [lead_id={lead.id}, {status_atual} -> {status_destino}, autor={autor}]")
        return True, f"Status alterado com sucesso para '{status_destino}'."


status_transition_service = StatusTransitionService()

import logging
from typing import Any
from datetime import datetime

from app.services.lead_service import lead_service, LeadEventoModel
from app.services.status_transition_service import status_transition_service

logger = logging.getLogger("alfaia.optout")


class OptOutService:
    """
    Detector de Opt-Out e Reversão LGPD S7 §22 (PRD §15.1, AC 1-4).
    - Palavras-chave de opt-out: STOP, PARAR, 'não quero mais receber', 'para de me mandar mensagem' (AC 1).
    - Marca `contato.opt_out=True` e bloqueia em campanhas (K3, AC 2).
    - Reversão espontânea quando o próprio titular volta a escrever (AC 3, AC 15.7).
    - Integra descarte automático do lead ativo (AC 4, AC 9.10).
    """

    PALAVRAS_CHAVE_OPTOUT = [
        "stop",
        "parar",
        "não quero mais receber",
        "nao quero mais receber",
        "para de me mandar mensagem",
        "pare de me mandar mensagem",
        "não mandar mais nada",
        "nao mandar mais nada",
        "cancelar cadastro",
    ]

    def eh_palavra_chave_optout(self, texto: str) -> bool:
        if not texto:
            return False
        texto_norm = texto.strip().lower()
        return any(kw in texto_norm for kw in self.PALAVRAS_CHAVE_OPTOUT)

    def detectar_e_processar_optout(
        self,
        tenant_id: str,
        contato_id: str,
        mensagem_texto: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        simulated_now = now or datetime.now()

        if not self.eh_palavra_chave_optout(mensagem_texto):
            return {"opt_out_detectado": False}

        # 1. Busca contato pelo id ou telefone
        contato = next((c for c in lead_service.contatos.values() if c.id == contato_id and c.tenant_id == tenant_id), None)
        if not contato:
            return {"opt_out_detectado": True, "sucesso": False, "erro": "Contato não encontrado"}

        # 2. Registra Opt-Out permanente (LGPD S7, AC 1, AC 2)
        contato.opt_out = True
        contato.opt_out_em = simulated_now
        if "opt_out" not in contato.tags:
            contato.tags.append("opt_out")

        # 3. Se houver lead ativo, executa descarte do lead com motivo 'opt_out' (AC 4, AC 9.10)
        lead_ativo = next((l for l in lead_service.leads if l.contato_id == contato_id and l.tenant_id == tenant_id and l.status not in ("ganho", "descartado")), None)
        lead_descartado_id = None
        if lead_ativo:
            status_transition_service.validar_e_mover_status(
                tenant_id=tenant_id,
                lead=lead_ativo,
                status_destino="descartado",
                autor="sistema",
                motivo="opt_out",
                now=simulated_now,
            )
            lead_descartado_id = lead_ativo.id

        # 4. Grava evento na timeline
        lead_service.eventos.append(
            LeadEventoModel(
                id=len(lead_service.eventos) + 1,
                tenant_id=tenant_id,
                lead_id=lead_descartado_id or f"optout_{contato_id}",
                tipo="opt_out_registrado",
                autor="sistema",
                motivo="Solicitação explícita de descadastro pelo titular (LGPD S7)",
                detalhe={"mensagem": mensagem_texto, "contato_id": contato_id},
                criado_em=simulated_now,
            )
        )

        logger.info(f"Opt-Out registrado com sucesso para o contato [contato_id={contato_id}, lead_descartado={lead_descartado_id}]")
        return {
            "opt_out_detectado": True,
            "sucesso": True,
            "contato_id": contato_id,
            "opt_out": True,
            "lead_descartado_id": lead_descartado_id,
        }

    def reverter_optout_se_espontaneo(
        self,
        tenant_id: str,
        contato_id: str,
        now: datetime | None = None,
    ) -> bool:
        """
        Reverte o opt-out quando o contato escreve espontaneamente (AC 3, AC 15.7, AC 9.14).
        """
        simulated_now = now or datetime.now()
        contato = next((c for c in lead_service.contatos.values() if c.id == contato_id and c.tenant_id == tenant_id), None)
        if not contato or not contato.opt_out:
            return False

        contato.opt_out = False
        contato.opt_out_em = None
        if "opt_out" in contato.tags:
            contato.tags.remove("opt_out")

        # Grava evento de reversão na timeline (AC 3)
        lead_service.eventos.append(
            LeadEventoModel(
                id=len(lead_service.eventos) + 1,
                tenant_id=tenant_id,
                lead_id=f"reversao_{contato_id}",
                tipo="opt_out_revertido",
                autor="sistema",
                motivo="Contato escreveu espontaneamente - consentimento renovado (AC 15.7)",
                criado_em=simulated_now,
            )
        )

        logger.info(f"Opt-Out revertido por mensagem espontânea do titular [contato_id={contato_id}]")
        return True


optout_service = OptOutService()

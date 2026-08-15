import logging
from typing import Any
from datetime import datetime

from app.services.lead_service import lead_service, LeadEventoModel

logger = logging.getLogger("alfaia.followup_dispatch")


class MensagemFollowupDTO:

    def __init__(self, id: str, nome: str, corpo: str, template_meta: str | None = None):
        self.id = id
        self.nome = nome
        self.corpo = corpo
        self.template_meta = template_meta


class FollowupDispatchService:
    """
    Serviço de Disparo Manual de Follow-up com Trava de Janela de 24h e Permissões de Papel (PRD §4.2, §10.2, AC 1-4).
    """

    def __init__(self):
        # Repositório em memória para mensagens de follow-up cadastradas (§17.8)
        self.mensagens_cadastradas: list[MensagemFollowupDTO] = [
            MensagemFollowupDTO(
                id="msg_1",
                nome="Lembrete Prova Vestido (Template Aprovado)",
                corpo="Olá! Gostaria de confirmar nossa data agendada para prova do seu vestido?",
                template_meta="template_lembrete_prova",
            ),
            MensagemFollowupDTO(
                id="msg_2",
                nome="Segunda Chamada Simples (Texto Livre)",
                corpo="Passando para saber se você ainda tem interesse nos modelos que enviamos!",
                template_meta=None,
            ),
        ]

    def disparar_followup(
        self,
        tenant_id: str,
        lead_id: str,
        mensagem_id: str,
        canal: str = "uazapi",
        janela_aberta: bool = True,
        user_role: str = "atendente",
        now: datetime | None = None,
    ) -> dict[str, Any]:
        simulated_now = now or datetime.now()

        # 1. Guard de Permissão de Papel: Apenas 'dono' e 'atendente' podem disparar follow-up; 'operador' é proibido (PRD §4.2, AC 3)
        if user_role not in ("dono", "atendente"):
            logger.warning(f"Disparo de follow-up negado por falta de permissão [role={user_role}]")
            return {
                "sucesso": False,
                "status_code": 403,
                "erro": "Permissão negada. Apenas usuários com perfil 'dono' ou 'atendente' podem disparar mensagens de follow-up.",
            }

        # 2. Busca mensagem cadastrada pelo ID
        msg = next((m for m in self.mensagens_cadastradas if m.id == mensagem_id), None)
        if not msg:
            return {"sucesso": False, "status_code": 404, "erro": f"Mensagem de follow-up '{mensagem_id}' não encontrada."}

        # 3. Gate de Janela de 24h do Canal Meta (AC 2, AC 10.6, §10.2):
        # Se canal for Meta e a janela de 24h estiver fechada, exige template_meta aprovado.
        if canal == "meta" and not janela_aberta:
            if not msg.template_meta:
                msg_erro = "Gate Meta 24h: Mensagens sem template aprovado são proibidas quando a janela da Meta está fechada."
                logger.warning(f"[REJEITADO GATE META] {msg_erro} [lead_id={lead_id}]")
                return {
                    "sucesso": False,
                    "status_code": 422,
                    "erro": msg_erro,
                }

        # 4. Busca lead e ajusta estado
        lead = next((l for l in lead_service.leads if l.id == lead_id and l.tenant_id == tenant_id), None)
        if lead:
            lead.status_alterado_em = simulated_now
            lead.status_alterado_por = "humano"

        # 5. Grava evento na timeline com autor='humano' (AC 1)
        lead_service.eventos.append(
            LeadEventoModel(
                id=len(lead_service.eventos) + 1,
                tenant_id=tenant_id,
                lead_id=lead_id,
                tipo="followup_enviado",
                de=lead.status if lead else "follow_up",
                para=lead.status if lead else "follow_up",
                autor="humano",
                detalhe={
                    "mensagem_id": msg.id,
                    "mensagem_nome": msg.nome,
                    "corpo": msg.corpo,
                    "canal": canal,
                    "template_meta": msg.template_meta,
                },
                criado_em=simulated_now,
            )
        )

        logger.info(f"Follow-up disparado com sucesso pelo lojista [lead_id={lead_id}, msg_id={msg.id}, canal={canal}]")
        return {
            "sucesso": True,
            "lead_id": lead_id,
            "mensagem_enviada": msg.corpo,
            "canal": canal,
            "template_utilizado": msg.template_meta,
            "autor": "humano",
        }


followup_dispatch_service = FollowupDispatchService()

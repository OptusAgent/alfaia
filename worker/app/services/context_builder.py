import logging
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

logger = logging.getLogger("alfaia.context_builder")


class ContatoDTO(BaseModel):
    id: str
    tenant_id: str
    nome: str | None = "Cliente"
    telefone: str
    primeiro_contato_em: str
    total_leads: int = 1
    tags: dict[str, Any] = Field(default_factory=dict)


class LeadDTO(BaseModel):
    id: str
    tenant_id: str
    contato_id: str
    lead_seq: int = 1
    status: str = "novo"
    origem: str = "whatsapp_organico"
    evento_tipo: str | None = None
    evento_data: str | None = None
    peca_interesse: str | None = None
    tamanho: str | None = None
    cor: str | None = None
    valor_estimado: float | None = None
    followup_tentativas: int = 0
    motivo_descarte: str | None = None
    ultimo_contato_em: datetime = Field(default_factory=datetime.now)
    criado_em: datetime = Field(default_factory=datetime.now)


class ContextBuilderService:
    """
    Montador de Contexto Estruturado do Lead (PRD §9.5, AC 9.3, 9.4).
    Assegura que o motor de IA receba sempre a visão completa do cliente e seu histórico.
    """

    @staticmethod
    def montar_contexto_lead(
        tipo_entrada: str,
        contato: ContatoDTO,
        lead_atual: LeadDTO,
        lead_anterior: LeadDTO | None = None,
        historico_mensagens: list[dict[str, Any]] | None = None,
        resumo_anterior: str | None = None,
        agendamentos: list[dict[str, Any]] | None = None,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        simulated_now = now or datetime.now()

        # Calcula dias em silêncio desde o último contato
        dias_silencio = (simulated_now - lead_atual.ultimo_contato_em).days
        if dias_silencio < 0:
            dias_silencio = 0

        # Trunca o histórico nas últimas 20 mensagens (AC 1, AC 2)
        msgs = historico_mensagens or []
        historico_recente = msgs[-20:] if len(msgs) > 20 else msgs

        # Montagem do objeto lead_anterior se existir (AC 3)
        lead_anterior_data = None
        if lead_anterior:
            lead_anterior_data = {
                "seq": lead_anterior.lead_seq,
                "status_final": lead_anterior.status,
                "motivo": lead_anterior.motivo_descarte or "encerrado",
                "evento_tipo": lead_anterior.evento_tipo,
                "evento_data": lead_anterior.evento_data,
                "peca_interesse": lead_anterior.peca_interesse,
                "encerrado_em": lead_anterior.ultimo_contato_em.strftime("%Y-%m-%d"),
            }

        # Contexto Estruturado no schema exato do PRD §9.5
        contexto = {
            "tipo_entrada": tipo_entrada,
            "contato": {
                "nome": contato.nome or "Cliente",
                "telefone": contato.telefone,
                "primeiro_contato_em": contato.primeiro_contato_em,
                "total_leads": contato.total_leads,
                "tags": contato.tags,
            },
            "lead_atual": {
                "id": lead_atual.id,
                "seq": lead_atual.lead_seq,
                "status": lead_atual.status,
                "evento_tipo": lead_atual.evento_tipo,
                "evento_data": lead_atual.evento_data,
                "peca_interesse": lead_atual.peca_interesse,
                "tamanho": lead_atual.tamanho,
                "cor": lead_atual.cor,
                "valor_estimado": lead_atual.valor_estimado,
                "dias_em_silencio": dias_silencio,
                "followup_tentativas": lead_atual.followup_tentativas,
            },
            "lead_anterior": lead_anterior_data,
            "historico_recente": historico_recente,
            "resumo_conversa_anterior": resumo_anterior or "",
            "agendamentos": agendamentos or [],
        }

        logger.info(f"Contexto montado com sucesso [tipo_entrada={tipo_entrada}, lead_seq={lead_atual.lead_seq}]")
        return contexto

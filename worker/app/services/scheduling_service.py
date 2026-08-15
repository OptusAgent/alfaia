import logging
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

from app.services.weblocacao_service import weblocacao_service, WLException

logger = logging.getLogger("alfaia.scheduling")


class AgendamentoModel(BaseModel):
    id: str
    tenant_id: str
    wl_agendamento_id: str
    lead_id: str
    tipo: str
    data: str
    hora: str
    cliente_nome: str
    cliente_telefone: str
    produto_ref: str | None = None
    origem: str = "automacao"
    status: str = "ativo"
    sincronizado_em: datetime = Field(default_factory=datetime.now)


class SchedulingService:
    """
    Serviço de Consulta de Slots e Agendamento Idempotente (PRD §7.2, §17.7, I6, AC 1-4).
    """

    def __init__(self):
        # Repositório de agendamentos para verificação de idempotência I6
        self.agendamentos: list[AgendamentoModel] = []

    def consultar_slots(
        self,
        tenant_id: str = "tenant_piloto",
        tipo: str = "prova",
        data_inicio: str = "2026-09-01",
        data_fim: str | None = None,
    ) -> dict[str, Any]:
        """
        Consulta vagas de atendimento em tempo real na WebLocação (AC 1).
        """
        try:
            slots = weblocacao_service.consultar_slots(tenant_id=tenant_id, tipo=tipo, data_inicio=data_inicio)
            return {
                "sucesso": True,
                "slots": [s.model_dump() for s in slots],
                "quantidade": len(slots),
                "mensagem": f"Encontramos {len(slots)} horários disponíveis para {tipo} em {data_inicio}.",
            }
        except Exception as e:
            logger.error(f"Erro ao consultar slots WL: {e}")
            return {
                "sucesso": False,
                "slots": [],
                "erro": str(e),
                "acao": "abrir_transbordo",
                "mensagem": "Não consegui verificar os horários no sistema. Vou transferir para nossa equipe.",
            }

    def agendar_prova_ou_retirada(
        self,
        tenant_id: str,
        lead_id: str,
        tipo: str,
        data: str,
        hora: str,
        cliente_nome: str,
        cliente_telefone: str,
        produto_ref: str | None = None,
        observacao: str | None = None,
        simular_erro_api: bool = False,
    ) -> dict[str, Any]:
        """
        Cria registro de agendamento na WebLocação com trava de escrita idempotente por (tenant_id, lead_id, data, hora) (I6, AC 2).
        """
        # 1. Trava de Idempotência: Se o mesmo lead já agendou para a mesma data/hora, não duplica no ERP (I6, AC 2)
        agendamento_existente = next(
            (
                a for a in self.agendamentos
                if a.tenant_id == tenant_id
                and a.lead_id == lead_id
                and a.data == data
                and a.hora == hora
                and a.status == "ativo"
            ),
            None,
        )

        if agendamento_existente:
            logger.info(f"Agendamento idempotente retornado sem duplicar reserva no ERP [id={agendamento_existente.id}]")
            return {
                "sucesso": True,
                "idempotente": True,
                "agendamento": agendamento_existente.model_dump(),
                "mensagem": f"Seu agendamento para {data} às {hora} já está confirmado no sistema.",
            }

        # 2. Tratamento de falha de escrita com transbordo (AC 4, I2, P3)
        if simular_erro_api:
            logger.error("Falha simulada na gravação de agendamento WebLocação. Acionando transbordo.")
            return {
                "sucesso": False,
                "acao": "abrir_transbordo",
                "mensagem": "Não consegui confirmar seu agendamento no sistema neste momento. Vou transferir para nossa equipe confirmar com você em breve.",
            }

        try:
            # 3. Invoca criação na WebLocação (Leitura e Escrita - PRD §7.1)
            dados_wl = {
                "tipo": tipo,
                "data": data,
                "hora": hora,
                "cliente_nome": cliente_nome,
                "cliente_telefone": cliente_telefone,
                "produto_id": produto_ref,
                "observacao": observacao,
            }
            res_wl = weblocacao_service.criar_agendamento(tenant_id=tenant_id, **dados_wl)

            # 4. Salva registro com wl_agendamento_id (PRD §17.7)
            novo_agendamento = AgendamentoModel(
                id=f"ag_{len(self.agendamentos) + 1}",
                tenant_id=tenant_id,
                wl_agendamento_id=res_wl.id,
                lead_id=lead_id,
                tipo=tipo,
                data=data,
                hora=hora,
                cliente_nome=cliente_nome,
                cliente_telefone=cliente_telefone,
                produto_ref=produto_ref,
                origem="automacao",
                status="ativo",
            )
            self.agendamentos.append(novo_agendamento)

            logger.info(f"Novo agendamento criado com sucesso [wl_id={res_wl.id}, local_id={novo_agendamento.id}]")
            return {
                "sucesso": True,
                "idempotente": False,
                "agendamento": novo_agendamento.model_dump(),
                "mensagem": f"Agendamento de {tipo} confirmado com sucesso para {data} às {hora}!",
            }

        except Exception as e:
            logger.error(f"Exceção capturada ao criar agendamento WL: {e}")
            return {
                "sucesso": False,
                "acao": "abrir_transbordo",
                "mensagem": "Ocorreu um imprevisto ao salvar seu agendamento. Nossa equipe dará continuidade ao atendimento.",
            }


scheduling_service = SchedulingService()

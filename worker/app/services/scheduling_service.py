import logging
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

from app.services.weblocacao_service import weblocacao_service, WLException
from app.services.supabase_rest import supabase_rest_service

logger = logging.getLogger("alfaia.scheduling")


def _fmt_data_br(data: str) -> str:
    """Converte data ISO (YYYY-MM-DD) para dd/mm/aaaa nas mensagens voltadas ao lead — a IA tende
    a repetir literalmente o texto real da tool (P3: nunca inventar), então se a mensagem trouxer
    a data em ISO, é isso que chega ao WhatsApp. Achado real em produção (2026-08-21). O campo
    `data` interno do agendamento (DB/idempotência) continua em ISO — só o texto muda."""
    try:
        return datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return data


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
                "mensagem": f"Encontramos {len(slots)} horários disponíveis para {tipo} em {_fmt_data_br(data_inicio)}.",
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

        # Fallback de idempotência via Postgres: cobre restart do processo/múltiplas réplicas,
        # onde a lista em memória de outra instância não teria visibilidade do agendamento
        # (story 5.6, AC 2). No-op silencioso se `supabase_rest_service` não estiver configurado.
        if not agendamento_existente:
            try:
                registro_db = supabase_rest_service.buscar_agendamento_ativo(tenant_id, lead_id, data, hora)
            except Exception as e:
                logger.warning(f"Falha inesperada ao consultar idempotencia em Postgres (nao bloqueante): {e}")
                registro_db = None
            if registro_db:
                agendamento_existente = AgendamentoModel(
                    id=registro_db["id"],
                    tenant_id=registro_db["tenant_id"],
                    wl_agendamento_id=registro_db.get("wl_agendamento_id") or "",
                    lead_id=registro_db["lead_id"],
                    tipo=registro_db["tipo"],
                    data=registro_db["data"],
                    hora=registro_db["hora"],
                    cliente_nome=registro_db.get("cliente_nome") or "",
                    cliente_telefone=registro_db.get("cliente_telefone") or "",
                    produto_ref=registro_db.get("produto_ref"),
                    origem=registro_db.get("origem", "automacao"),
                    status=registro_db.get("status", "ativo"),
                )
                self.agendamentos.append(agendamento_existente)

        if agendamento_existente:
            logger.info(f"Agendamento idempotente retornado sem duplicar reserva no ERP [id={agendamento_existente.id}]")
            return {
                "sucesso": True,
                "idempotente": True,
                "agendamento": agendamento_existente.model_dump(),
                "mensagem": f"Seu agendamento para {_fmt_data_br(data)} às {hora} já está confirmado no sistema.",
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

            # 5. Persiste em Postgres real (story 5.6, AC 2, AC 4) — só depois do WL confirmar (nunca o
            # inverso). Falha aqui não desfaz o agendamento já confirmado no ERP nem quebra a resposta
            # ao lead: fica auditável pelo log de erro para investigação, sem prometer nada de novo a ele.
            try:
                registro_persistido = supabase_rest_service.inserir_agendamento(
                    {
                        # "id" omitido de propósito: a coluna tem default gen_random_uuid() no Postgres;
                        # o "id" do AgendamentoModel local (ex. "ag_1") é só a chave da lista em memória.
                        "tenant_id": tenant_id,
                        "wl_agendamento_id": res_wl.id,
                        "lead_id": lead_id,
                        "tipo": tipo,
                        "data": data,
                        "hora": hora,
                        "cliente_nome": cliente_nome,
                        "cliente_telefone": cliente_telefone,
                        "produto_ref": produto_ref,
                        "origem": "automacao",
                        "status": "ativo",
                    }
                )
            except Exception as e:
                logger.error(f"Falha inesperada ao persistir agendamento (nao bloqueante): {e}")
                registro_persistido = None
            if registro_persistido is None and supabase_rest_service.configurado:
                logger.error(
                    f"Agendamento confirmado no WL (wl_id={res_wl.id}) mas NAO foi possivel persistir em "
                    f"agendamentos — investigar manualmente [tenant={tenant_id}, lead={lead_id}, data={data} {hora}]."
                )

            logger.info(f"Novo agendamento criado com sucesso [wl_id={res_wl.id}, local_id={novo_agendamento.id}]")
            return {
                "sucesso": True,
                "idempotente": False,
                "agendamento": novo_agendamento.model_dump(),
                "mensagem": f"Agendamento de {tipo} confirmado com sucesso para {_fmt_data_br(data)} às {hora}!",
            }

        except Exception as e:
            logger.error(f"Exceção capturada ao criar agendamento WL: {e}")
            return {
                "sucesso": False,
                "acao": "abrir_transbordo",
                "mensagem": "Ocorreu um imprevisto ao salvar seu agendamento. Nossa equipe dará continuidade ao atendimento.",
            }


scheduling_service = SchedulingService()

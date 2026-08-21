import logging
from datetime import datetime, timedelta
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

    # Máximo de dias corridos varridos ao procurar disponibilidade real (próximos dias ou
    # alternativa mais próxima) — evita busca sem fim se uma agenda ficar fechada por muito tempo.
    # Cada dia varrido é 1 chamada HTTP real (timeout 8s, retry 2x em 5xx — até ~24s no pior caso)
    # ao adapter real da WebLocação; mantido baixo de propósito (achado de revisão, 2026-08-21) —
    # o caso feliz encontra os 5 dias já na primeira semana (só domingo fecha), e um teto alto
    # vira risco real de travar a resposta do webhook se a API da WL estiver degradada.
    MAX_DIAS_BUSCA_DISPONIBILIDADE = 10

    def _dias_com_vaga_real(
        self, tenant_id: str, tipo: str, data_referencia: str, max_dias: int = 5
    ) -> list[dict[str, Any]]:
        """
        Varre dia a dia a partir de `data_referencia` (inclusive) e devolve até `max_dias` dias
        que têm pelo menos 1 horário real com vaga livre — nunca inventa disponibilidade: um dia
        fechado (sem `horarios_funcionamento`) ou lotado (vagas_livres=0 em todos os horários)
        simplesmente não entra na lista (achado real em produção, 2026-08-21: agendamento sem
        nenhuma verificação de agenda real, data/hora efetivamente inventadas pelo modelo).
        """
        try:
            base = datetime.strptime(data_referencia, "%Y-%m-%d")
        except (ValueError, TypeError):
            base = datetime.now()

        dias: list[dict[str, Any]] = []
        for i in range(self.MAX_DIAS_BUSCA_DISPONIBILIDADE):
            dia_str = (base + timedelta(days=i)).strftime("%Y-%m-%d")
            try:
                slots = weblocacao_service.consultar_slots(tenant_id=tenant_id, tipo=tipo, data_inicio=dia_str)
            except Exception as e:
                logger.warning(f"Falha ao consultar slots do dia {dia_str} na varredura de disponibilidade: {e}")
                continue
            livres = [s.hora for s in slots if s.vagas_livres > 0]
            if livres:
                dias.append({"data": dia_str, "horarios": livres})
            if len(dias) >= max_dias:
                break
        return dias

    def consultar_slots(
        self,
        tenant_id: str = "tenant_piloto",
        tipo: str = "prova",
        data_inicio: str | None = None,
        data_fim: str | None = None,
    ) -> dict[str, Any]:
        """
        Consulta vagas reais de atendimento na WebLocação (AC 1). Sem `data_inicio` (lead ainda
        não tem preferência de dia), devolve os próximos dias reais com horário livre a partir de
        hoje. Com `data_inicio` (lead propôs um dia), devolve os horários reais daquele dia — se
        esse dia não tiver nenhum horário livre (fechado ou lotado), devolve os dias mais próximos
        com vaga real em vez de inventar ou silenciosamente escolher uma data (ajuste de agenda,
        2026-08-21, achado real: agendamento confirmado numa data/hora nunca verificada).
        """
        try:
            if not data_inicio:
                dias = self._dias_com_vaga_real(tenant_id, tipo, datetime.now().strftime("%Y-%m-%d"))
                return {
                    "sucesso": True,
                    "slots": [],
                    "dias_disponiveis": dias,
                    "mensagem": (
                        f"Próximos {len(dias)} dias com horário disponível para {tipo}."
                        if dias
                        else f"Não encontrei horário disponível para {tipo} nos próximos {self.MAX_DIAS_BUSCA_DISPONIBILIDADE} dias."
                    ),
                }

            slots = weblocacao_service.consultar_slots(tenant_id=tenant_id, tipo=tipo, data_inicio=data_inicio)
            livres = [s for s in slots if s.vagas_livres > 0]
            if livres:
                return {
                    "sucesso": True,
                    "slots": [s.model_dump() for s in slots],
                    "quantidade": len(livres),
                    "data_pedida_disponivel": True,
                    "mensagem": f"Encontramos {len(livres)} horários disponíveis para {tipo} em {_fmt_data_br(data_inicio)}.",
                }

            # Data pedida sem nenhuma vaga real (fechado ou lotado) — busca os dias mais próximos
            # com disponibilidade real, começando pela própria data pedida (inclusive), nunca
            # inventando nem escolhendo uma data sozinho.
            dias_alternativos = self._dias_com_vaga_real(tenant_id, tipo, data_inicio)
            return {
                "sucesso": True,
                "slots": [],
                "quantidade": 0,
                "data_pedida_disponivel": False,
                "dias_disponiveis": dias_alternativos,
                "mensagem": (
                    f"Não há horário disponível para {tipo} em {_fmt_data_br(data_inicio)}. "
                    f"Dia real mais próximo com vaga: {_fmt_data_br(dias_alternativos[0]['data'])}."
                    if dias_alternativos
                    else f"Não há horário disponível para {tipo} em {_fmt_data_br(data_inicio)} nem nos próximos dias pesquisados."
                ),
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
                "agendado": True,
                "idempotente": True,
                "agendamento": agendamento_existente.model_dump(),
                "mensagem": f"Seu agendamento para {_fmt_data_br(data)} às {hora} já está confirmado no sistema.",
            }

        # 1.5 Verificação real de agenda (achado real em produção, 2026-08-21): `agendar` nunca
        # confirmava se `data`/`hora` correspondiam a um horário real com vaga — o modelo podia
        # (e chegou a) inventar uma data/hora sem nunca ter consultado `consultar_slots` na
        # conversa. Aqui é a garantia dura (P3, mesmo padrão de outros "nunca confiar só na
        # instrução de prompt"): revalida contra a agenda real no momento da escrita. Se não bater
        # com um horário livre de verdade, NÃO cria o agendamento — devolve `sucesso: True` (não é
        # falha de sistema, não aciona transbordo) com `agendado: False` e a data real mais
        # próxima com vaga, para a IA reoferecer sem inventar nada.
        try:
            slots_do_dia = weblocacao_service.consultar_slots(tenant_id=tenant_id, tipo=tipo, data_inicio=data)
        except Exception as e:
            logger.warning(f"Falha ao revalidar agenda antes de agendar (nao bloqueante, segue sem validar): {e}")
            slots_do_dia = None
        if slots_do_dia is not None:
            slot_valido = next((s for s in slots_do_dia if s.hora == hora and s.vagas_livres > 0), None)
            if slot_valido is None:
                dias_alternativos = self._dias_com_vaga_real(tenant_id, tipo, data)
                proxima = dias_alternativos[0] if dias_alternativos else None
                return {
                    "sucesso": True,
                    "agendado": False,
                    "motivo": "horario_indisponivel",
                    "dias_disponiveis": dias_alternativos,
                    "mensagem": (
                        f"O horário {hora} de {_fmt_data_br(data)} não está mais disponível para {tipo}. "
                        + (
                            f"O dia real mais próximo com vaga é {_fmt_data_br(proxima['data'])}, horários: {', '.join(proxima['horarios'])}."
                            if proxima
                            else "Não encontrei outro horário disponível nos próximos dias pesquisados."
                        )
                    ),
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
                "agendado": True,
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

import logging
import random
from datetime import datetime, timedelta
from typing import Any

from app.services.lead_service import lead_service, LeadEventoModel, ContatoModel, LeadModel

logger = logging.getLogger("alfaia.campanha_engine")


class AlvoModel:

    def __init__(self, id: int, campanha_id: str, contato_id: str, status: str = "pendente"):
        self.id = id
        self.campanha_id = campanha_id
        self.contato_id = contato_id
        self.status = status  # 'pendente', 'enviado', 'falha', 'ignorado_optout', 'ignorado_15dias'
        self.wa_message_id: str | None = None
        self.enviado_em: datetime | None = None


class CampanhaEngineService:
    """
    Motor de Disparo e Proteção Operacional de Campanhas (PRD §15.2, K1-K8, AC 1-8).
    - K1: UAZAPI delay 5-15s, presence composing, horário comercial 08h-20h (AC 1).
    - K2: Meta template obrigatório, sem delay artificial (AC 2).
    - K3: Trava estrita de opt-out no disparo real (AC 3).
    - K4: Trava de 15 dias entre campanhas por contato (AC 4).
    - K5: Resposta cria/reabre lead com origem 'campanha' (AC 5).
    - K6: Pausa e retomada preservando fila (AC 6).
    - K7: Aquecimento UAZAPI max 200 envios/dia nos primeiros 7 dias (AC 7).
    - K8: Auto-pausa quando taxa de falha > 15% em 50 envios (AC 8).
    """

    def __init__(self):
        self.alvos: list[AlvoModel] = []
        # Histórico de envios para K4 (contato_id -> datetime ultimo envio)
        self.historico_envios_contato: dict[str, datetime] = {}
        # Contador diário para K7 aquecimento (data_str -> contador)
        self.envios_diarios_aquecimento: dict[str, int] = {}

    def eh_horario_comercial(self, now: datetime) -> bool:
        """Verifica se está dentro do horário comercial (08:00 às 20:00) (K1)."""
        return 8 <= now.hour < 20

    def verificar_aquecimento_limite_200(self, tenant_id: str, now: datetime) -> bool:
        """K7: UAZAPI máx 200 envios/dia nos primeiros 7 dias de número novo."""
        chave_dia = now.strftime("%Y-%m-%d")
        total_hoje = self.envios_diarios_aquecimento.get(chave_dia, 0)
        return total_hoje < 200

    def verificar_limite_15_dias_contato(self, contato_id: str, now: datetime) -> bool:
        """K4: Limite de 1 campanha por contato a cada 15 dias."""
        ultimo_envio = self.historico_envios_contato.get(contato_id)
        if not ultimo_envio:
            return True
        return (now - ultimo_envio) >= timedelta(days=15)

    def iniciar_campanha(self, campanha_id: str, tenant_id: str = "tenant_piloto") -> dict[str, Any]:
        """Inicia a campanha criando a fila de alvos elegíveis (K6)."""
        from app.services.campanha_service import campanha_service
        camp = next((c for c in campanha_service.campanhas if c.id == campanha_id), None)
        if not camp:
            return {"sucesso": False, "erro": f"Campanha {campanha_id} não encontrada"}

        camp.status = "em_execucao"

        # Popula alvos pendentes na memória
        contatos_elegiveis = [c for c in lead_service.contatos.values() if c.tenant_id == tenant_id]
        for c in contatos_elegiveis:
            self.alvos.append(AlvoModel(id=len(self.alvos) + 1, campanha_id=campanha_id, contato_id=c.id))

        logger.info(f"Campanha iniciada [campanha_id={campanha_id}, total_alvos={len(self.alvos)}]")
        return {"sucesso": True, "status": "em_execucao", "total_alvos": len(self.alvos)}

    def pausar_campanha(self, campanha_id: str, motivo: str = "Pausa manual pelo lojista") -> dict[str, Any]:
        """K6, K8: Pausa a campanha preservando a fila de alvos."""
        from app.services.campanha_service import campanha_service
        camp = next((c for c in campanha_service.campanhas if c.id == campanha_id), None)
        if camp:
            camp.status = "pausada"
            camp.pausada_motivo = motivo
            logger.info(f"Campanha pausada [campanha_id={campanha_id}, motivo='{motivo}']")
            return {"sucesso": True, "status": "pausada", "motivo": motivo}
        return {"sucesso": False, "erro": "Campanha não encontrada"}

    def retomar_campanha(self, campanha_id: str) -> dict[str, Any]:
        """K6: Retoma a campanha pausada de onde parou."""
        from app.services.campanha_service import campanha_service
        camp = next((c for c in campanha_service.campanhas if c.id == campanha_id), None)
        if camp:
            camp.status = "em_execucao"
            camp.pausada_motivo = None
            logger.info(f"Campanha retomada [campanha_id={campanha_id}]")
            return {"sucesso": True, "status": "em_execucao"}
        return {"sucesso": False, "erro": "Campanha não encontrada"}

    def processar_proximo_disparo(
        self,
        campanha_id: str,
        canal: str = "uazapi",
        is_em_aquecimento: bool = True,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        from app.services.campanha_service import campanha_service
        simulated_now = now or datetime.now()
        camp = next((c for c in campanha_service.campanhas if c.id == campanha_id), None)
        if not camp or camp.status != "em_execucao":
            return {"sucesso": False, "motivo": "Campanha não está em execução"}

        alvo = next((a for a in self.alvos if a.campanha_id == campanha_id and a.status == "pendente"), None)
        if not alvo:
            camp.status = "concluida"
            return {"sucesso": True, "concluida": True, "mensagem": "Todos os alvos foram processados"}

        contato = next((c for c in lead_service.contatos.values() if c.id == alvo.contato_id), None)
        if not contato:
            alvo.status = "falha"
            camp.falhas += 1
            return {"sucesso": False, "erro": "Contato não encontrado"}

        # 1. K3: Filtro estrito de Opt-Out no momento do disparo (AC 3)
        if contato.opt_out:
            alvo.status = "ignorado_optout"
            logger.info(f"K3 acionado: disparo ignorado por opt-out [contato_id={contato.id}]")
            return {"sucesso": False, "regra": "K3", "motivo": "Contato em Opt-Out"}

        # 2. K4: Trava de 15 dias por contato (AC 4)
        if not self.verificar_limite_15_dias_contato(contato.id, simulated_now):
            alvo.status = "ignorado_15dias"
            logger.info(f"K4 acionado: disparo ignorado por limite de 15 dias [contato_id={contato.id}]")
            return {"sucesso": False, "regra": "K4", "motivo": "Limite de 15 dias entre campanhas"}

        # 3. K7: Aquecimento UAZAPI max 200/dia (AC 7)
        if canal == "uazapi" and is_em_aquecimento:
            if not self.verificar_aquecimento_limite_200(camp.tenant_id, simulated_now):
                logger.warning(f"K7 acionado: limite de aquecimento diário (200 envios) atingido no UAZAPI")
                return {"sucesso": False, "regra": "K7", "motivo": "Limite de aquecimento 200/dia atingido"}

        # 4. K1: Horário Comercial UAZAPI (AC 1)
        if canal == "uazapi" and not self.eh_horario_comercial(simulated_now):
            logger.info(f"K1 acionado: fora do horário comercial (08h-20h)")
            return {"sucesso": False, "regra": "K1", "motivo": "Fora do horário comercial"}

        # Simula delay 5-15s K1 e presence composing
        delay = random.randint(5, 15) if canal == "uazapi" else 0

        # Executa Envio
        alvo.status = "enviado"
        alvo.enviado_em = simulated_now
        alvo.wa_message_id = f"wa_msg_{alvo.id}"
        camp.enviados += 1

        # Atualiza histórico K4 e contador K7
        self.historico_envios_contato[contato.id] = simulated_now
        chave_dia = simulated_now.strftime("%Y-%m-%d")
        self.envios_diarios_aquecimento[chave_dia] = self.envios_diarios_aquecimento.get(chave_dia, 0) + 1

        # 5. K8: Auto-pausa se taxa de falha > 15% em >= 50 envios (AC 8)
        total_processados = camp.enviados + camp.falhas
        if total_processados >= 50:
            taxa_falha = (camp.falhas / total_processados) * 100.0
            if taxa_falha > 15.0:
                self.pausar_campanha(campanha_id=campanha_id, motivo="auto_pausa_falha_15_porcento")
                lead_service.eventos.append(
                    LeadEventoModel(
                        id=len(lead_service.eventos) + 1,
                        tenant_id=camp.tenant_id,
                        lead_id=f"campanha_{campanha_id}",
                        tipo="alerta_campanha_pausada",
                        autor="sistema",
                        motivo=f"K8 acionado: taxa de falha ({taxa_falha:.1f}%) excedeu 15% em {total_processados} envios.",
                        criado_em=simulated_now,
                    )
                )
                logger.error(f"K8 ACIONADO: Campanha {campanha_id} pausada automaticamente por taxa de falhas excedente ({taxa_falha:.1f}%)")

        return {
            "sucesso": True,
            "alvo_id": alvo.id,
            "contato_id": contato.id,
            "delay_aplicado_segundos": delay,
            "presence": "composing" if canal == "uazapi" else None,
        }

    def correlacionar_resposta_campanha(self, tenant_id: str, contato_id: str, mensagem_texto: str, now: datetime | None = None) -> dict[str, Any]:
        """K5: Resposta a campanha cria/reabre lead com origem 'campanha' (AC 5, PRD §15.2)."""
        simulated_now = now or datetime.now()
        contato = next((c for c in lead_service.contatos.values() if c.id == contato_id and c.tenant_id == tenant_id), None)
        if not contato:
            return {"sucesso": False, "erro": "Contato não encontrado"}

        # Invoca identificar_lead com origem='campanha'
        contato_id_res, lead_id, tipo_entrada = lead_service.identificar_lead(
            tenant_id=tenant_id,
            telefone=contato.telefone,
            push_name=contato.nome or "Cliente",
            origem="campanha",  # K5
            simulated_now=simulated_now,
        )

        from app.services.campanha_service import campanha_service
        camp = next((c for c in campanha_service.campanhas if c.tenant_id == tenant_id and c.status in ("em_execucao", "concluida")), None)
        if camp:
            camp.respondidos += 1

        logger.info(f"K5 executado: resposta a campanha gerou lead com origem='campanha' [lead_id={lead_id}]")
        return {"sucesso": True, "lead_id": lead_id, "tipo_entrada": tipo_entrada, "origem": "campanha"}


campanha_engine_service = CampanhaEngineService()

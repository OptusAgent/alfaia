import logging
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger("alfaia.handoff_service")

# 5 Gatilhos de Transbordo Humano (PRD §13.1)
GATILHO_PEDIDO_EXPLICITO = "pedido_explicito_lead"
GATILHO_ASSUNTO_CRITICO = "assunto_critico_ia"
GATILHO_FALHA_CONSECUTIVA = "falha_consecutiva_3x"
GATILHO_ERRO_SISTEMA = "erro_integracao_sistema"
GATILHO_OPERADOR_HUMANO = "atendente_assumiu_manual"


class HandoffService:
    """
    Serviço Completo de Transbordo Humano, Pausa Renovável e Expiração Automática (PRD §13.1, §13.2, §17.5, AC 1-6).
    """

    @staticmethod
    def classificar_gatilho_transbordo(
        texto: str | None = None,
        erros_consecutivos: int = 0,
        erro_sistema: bool = False,
    ) -> tuple[bool, str | None]:
        """
        Classifica se a mensagem/contexto aciona um dos 5 gatilhos de transbordo humano (PRD §13.1).
        """
        if erro_sistema:
            return True, GATILHO_ERRO_SISTEMA

        if erros_consecutivos >= 3:
            return True, GATILHO_FALHA_CONSECUTIVA

        if texto:
            texto_lower = texto.lower()
            if any(termo in texto_lower for termo in ["humano", "atendente", "falar com pessoa", "atendimento humano"]):
                return True, GATILHO_PEDIDO_EXPLICITO

            if any(termo in texto_lower for termo in ["avaria", "processo", "advogado", "jurídico", "urgência", "reclamação grave"]):
                return True, GATILHO_ASSUNTO_CRITICO

        return False, None

    @classmethod
    def conversa_esta_pausada(cls, conversa: dict[str, Any] | None, now: datetime | None = None) -> bool:
        """
        Verifica se a conversa está pausada por um atendente humano ou em transbordo.
        Retorna False caso a pausa de 30 min já tenha expirado sem ação (AC 4, AC 13.4).
        """
        if not conversa:
            return False

        estado = conversa.get("estado", "ia")
        pausada_ate = conversa.get("pausada_ate")
        simulated_now = now or datetime.now()

        if estado in ("humano", "transbordo"):
            if pausada_ate:
                if isinstance(pausada_ate, str):
                    pausada_ate = datetime.fromisoformat(pausada_ate)
                if simulated_now > pausada_ate:
                    logger.info(f"Pausa de conversa expirada sem ação. Retomando IA [conversa_id={conversa.get('id')}]")
                    return False
            return True

        return False

    @classmethod
    def deve_executar_ia(cls, conversa: dict[str, Any] | None, now: datetime | None = None) -> bool:
        """
        Se a conversa estiver pausada ou em transbordo ativo, a IA é silenciada (AC 8.6).
        """
        executar = not cls.conversa_esta_pausada(conversa, now=now)
        if not executar:
            logger.info("Execução da IA silenciada: Conversa em modo HUMANO / TRANSBORDO ativo.")
        return executar

    @staticmethod
    def assumir_conversa(
        conversa: dict[str, Any],
        atendente_id: str,
        pausa_minutos: int = 30,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Atendente humano assume a conversa no Portal, pausando a IA por 30 minutos (AC 2, AC 13.2).
        """
        simulated_now = now or datetime.now()
        conversa["estado"] = "humano"
        conversa["pausada_em"] = simulated_now
        conversa["pausada_por"] = atendente_id
        conversa["pausada_ate"] = simulated_now + timedelta(minutes=pausa_minutos)

        logger.info(f"Conversa assumida [id={conversa.get('id')}, atendente={atendente_id}, pausada_ate={conversa['pausada_ate']}]")
        return conversa

    @staticmethod
    def renovar_pausa_humana(
        conversa: dict[str, Any],
        pausa_minutos: int = 30,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Renova a pausa de 30 minutos a cada nova mensagem enviada pelo atendente humano (AC 2, AC 13.2).
        """
        simulated_now = now or datetime.now()
        if conversa.get("estado") == "humano":
            conversa["pausada_ate"] = simulated_now + timedelta(minutes=pausa_minutos)
            logger.info(f"Pausa renovada por mensagem do atendente [id={conversa.get('id')}, novo_pausada_ate={conversa['pausada_ate']}]")
        return conversa

    @staticmethod
    def devolver_para_ia(
        conversa: dict[str, Any],
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Atendente devolve a conversa para a IA, encerrando a pausa imedatamente (AC 3, AC 13.3).
        """
        simulated_now = now or datetime.now()
        conversa["estado"] = "ia"
        conversa["pausada_em"] = None
        conversa["pausada_por"] = None
        conversa["pausada_ate"] = None
        conversa["ativada_em"] = simulated_now

        logger.info(f"Conversa devolvida para IA [conversa_id={conversa.get('id')}]")
        return conversa

    @classmethod
    def processar_expiracao_pausas_lote(
        cls,
        conversas: list[dict[str, Any]],
        now: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """
        Job 'transbordo_expirar' (§18.3): Expira pausas ativas onde now > pausada_ate e retoma a IA (AC 4, AC 13.4).
        """
        simulated_now = now or datetime.now()
        retomadas = []

        for conv in conversas:
            estado = conv.get("estado")
            pausada_ate = conv.get("pausada_ate")

            if estado in ("humano", "transbordo") and pausada_ate:
                if isinstance(pausada_ate, str):
                    pausada_ate = datetime.fromisoformat(pausada_ate)

                if simulated_now > pausada_ate:
                    cls.devolver_para_ia(conv, now=simulated_now)
                    retomadas.append(conv)
                    logger.info(f"Retomada automática de IA executada para conversa pausada [id={conv.get('id')}]")

        return retomadas


handoff_service = HandoffService()

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger("alfaia.handoff_service")


class HandoffService:
    """
    Serviço de Gestão de Transbordo Humano e Pausa da IA (PRD §17.12, AC 1, AC 8.6).
    """

    @staticmethod
    def conversa_esta_pausada(conversa: dict[str, Any] | None) -> bool:
        """
        Verifica se a conversa está pausada por um atendente humano ou em transbordo.
        """
        if not conversa:
            return False

        estado = conversa.get("estado", "ia")
        pausada_em = conversa.get("pausada_em")

        if estado in ("humano", "transbordo") or pausada_em is not None:
            return True

        return False

    @classmethod
    def deve_executar_ia(cls, conversa: dict[str, Any] | None) -> bool:
        """
        Se a conversa estiver pausada ou em transbordo, a IA é silenciada (AC 8.6).
        Mensagens continuam sendo salvas e exibidas no portal normalmente.
        """
        executar = not cls.conversa_esta_pausada(conversa)
        if not executar:
            logger.info("Execução da IA silenciada: Conversa em modo HUMANO / TRANSBORDO.")
        return executar

    @staticmethod
    def assumir_conversa(
        conversa: dict[str, Any],
        atendente_id: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Atendente humano assume o controle da conversa no Portal.
        """
        simulated_now = now or datetime.now()
        conversa["estado"] = "humano"
        conversa["pausada_em"] = simulated_now
        conversa["atendente_id"] = atendente_id

        logger.info(f"Conversa assumida por atendente humano [conversa_id={conversa.get('id')}, atendente_id={atendente_id}]")
        return conversa

    @staticmethod
    def devolver_para_ia(
        conversa: dict[str, Any],
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Devolve o atendimento para a IA.
        """
        simulated_now = now or datetime.now()
        conversa["estado"] = "ia"
        conversa["pausada_em"] = None
        conversa["ativada_em"] = simulated_now

        logger.info(f"Conversa devolvida para o atendimento da IA [conversa_id={conversa.get('id')}]")
        return conversa


handoff_service = HandoffService()

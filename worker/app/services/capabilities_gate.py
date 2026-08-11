from typing import Any
from app.adapters.base import Capabilities


class CapabilitiesGate:
    """
    Gate server-side de validação de capacidades do canal ativo (PRD §14.3, AC 14.5).
    Bloqueia envio de texto livre server-side se janela_24h=True e a janela estiver fechada.
    """

    @staticmethod
    def validar_envio_mensagem(
        capabilities: Capabilities,
        janela_24h_aberta: bool,
        tipo_mensagem: str = "text",
    ) -> dict[str, Any]:
        """
        Consulta `capabilities` antes de enviar:
        canal com `janela_24h` e janela fechada → texto livre bloqueado server-side,
        UI orienta ao uso de template (PRD §14.3, AC 4).
        """
        if capabilities.janela_24h and not janela_24h_aberta and tipo_mensagem == "text":
            return {
                "permitido": False,
                "codigo": "FECHADO_24H",
                "mensagem": "Envio de texto livre bloqueado: a janela de 24h deste canal está fechada. Utilize um modelo de mensagem (template).",
            }

        return {"permitido": True}

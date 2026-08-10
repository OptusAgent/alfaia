from dataclasses import dataclass
from typing import Literal, Protocol, Any, runtime_checkable
from pydantic import BaseModel, Field


@dataclass(frozen=True)
class Capabilities:
    """Capacidades e restrições operacionais do canal de comunicação (PRD §14.2)."""
    janela_24h: bool
    suporta_template: bool
    requer_delay: bool
    delay_min_ms: int
    delay_max_ms: int
    exige_horario_comercial: bool


class PayloadNormalizado(BaseModel):
    """Contrato interno de mensagem normalizada recebida via webhook (PRD §6.3)."""
    tenant_id: str
    canal_id: str
    provider: Literal["uazapi", "meta", "fake"]
    telefone: str  # Apenas dígitos com DDI, ex: 5585988124477
    push_name: str
    mensagem: str
    midia_url: str | None = None
    midia_tipo: Literal["text", "audio", "image", "document"] = "text"
    wa_message_id: str
    timestamp: int
    data_atual: str


class ResultadoEnvio(BaseModel):
    """Resultado retornado após a tentativa de envio de uma mensagem (PRD §14.2)."""
    sucesso: bool
    wa_message_id: str | None = None
    erro: str | None = None


@runtime_checkable
class CanalAdapter(Protocol):
    """Protocolo/Interface agnóstica para provedores de canal WhatsApp (PRD §14.2)."""


    def normalizar_webhook(self, raw: bytes, headers: dict[str, Any]) -> list[PayloadNormalizado]:
        ...

    async def enviar_texto(self, to: str, text: str) -> ResultadoEnvio:
        ...

    async def enviar_midia(
        self, to: str, url: str, tipo: str, caption: str | None = None
    ) -> ResultadoEnvio:
        ...

    async def enviar_template(
        self, to: str, nome: str, idioma: str, componentes: list[dict[str, Any]]
    ) -> ResultadoEnvio:
        ...

    async def marcar_lido(self, wa_message_id: str) -> None:
        ...

    @property
    def capabilities(self) -> Capabilities:
        ...

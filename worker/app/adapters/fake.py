import json
import uuid
from typing import Any
from app.adapters.base import CanalAdapter, Capabilities, PayloadNormalizado, ResultadoEnvio
from app.adapters.phone import normalizar_telefone


class FakeCanalAdapter:
    """
    Adapter Fake/In-Memory para uso em testes unitários e de integração (PRD §14.2, AC 3).
    Garante compliance estrito com o protocolo CanalAdapter sem depender de APIs externas.
    """

    def __init__(
        self,
        tenant_id: str = "00000000-0000-0000-0000-000000000001",
        canal_id: str = "00000000-0000-0000-0000-000000000002",
        capabilities: Capabilities | None = None,
    ):
        self.tenant_id = tenant_id
        self.canal_id = canal_id
        self._capabilities = capabilities or Capabilities(
            janela_24h=False,
            suporta_template=True,
            requer_delay=False,
            delay_min_ms=0,
            delay_max_ms=0,
            exige_horario_comercial=False,
        )
        self.mensagens_enviadas: list[dict[str, Any]] = []
        self.mensagens_lidas: list[str] = []

    @property
    def capabilities(self) -> Capabilities:
        return self._capabilities

    def normalizar_webhook(self, raw: bytes, headers: dict[str, Any]) -> list[PayloadNormalizado]:
        """Converte JSON cru de webhook num PayloadNormalizado fictício."""
        data = json.loads(raw.decode("utf-8")) if raw else {}
        telefone = normalizar_telefone(data.get("telefone", "5585988124477"))
        
        payload = PayloadNormalizado(
            tenant_id=self.tenant_id,
            canal_id=self.canal_id,
            provider="fake",
            telefone=telefone,
            push_name=data.get("push_name", "Cliente Teste"),
            mensagem=data.get("mensagem", "Olá, mensagem de teste"),
            midia_url=data.get("midia_url"),
            midia_tipo=data.get("midia_tipo", "text"),
            wa_message_id=data.get("wa_message_id", f"fake_msg_{uuid.uuid4().hex[:10]}"),
            timestamp=data.get("timestamp", 1754570000),
            data_atual=data.get("data_atual", "Sexta-feira, 7 de agosto de 2026, 14:32"),
        )
        return [payload]

    async def enviar_texto(self, to: str, text: str) -> ResultadoEnvio:
        wa_id = f"fake_wamid_{uuid.uuid4().hex[:12]}"
        registro = {
            "tipo": "texto",
            "to": normalizar_telefone(to),
            "text": text,
            "wa_message_id": wa_id,
        }
        self.mensagens_enviadas.append(registro)
        return ResultadoEnvio(sucesso=True, wa_message_id=wa_id)

    async def enviar_midia(
        self, to: str, url: str, tipo: str, caption: str | None = None
    ) -> ResultadoEnvio:
        wa_id = f"fake_wamid_{uuid.uuid4().hex[:12]}"
        registro = {
            "tipo": "midia",
            "to": normalizar_telefone(to),
            "url": url,
            "midia_tipo": tipo,
            "caption": caption,
            "wa_message_id": wa_id,
        }
        self.mensagens_enviadas.append(registro)
        return ResultadoEnvio(sucesso=True, wa_message_id=wa_id)

    async def enviar_template(
        self, to: str, nome: str, idioma: str, componentes: list[dict[str, Any]]
    ) -> ResultadoEnvio:
        wa_id = f"fake_wamid_{uuid.uuid4().hex[:12]}"
        registro = {
            "tipo": "template",
            "to": normalizar_telefone(to),
            "nome": nome,
            "idioma": idioma,
            "componentes": componentes,
            "wa_message_id": wa_id,
        }
        self.mensagens_enviadas.append(registro)
        return ResultadoEnvio(sucesso=True, wa_message_id=wa_id)

    async def marcar_lido(self, wa_message_id: str) -> None:
        self.mensagens_lidas.append(wa_message_id)


# Assegura estritamente que FakeCanalAdapter satisfaz o Protocol CanalAdapter
_check_protocol: CanalAdapter = FakeCanalAdapter()

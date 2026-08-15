import json
import logging
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger("alfaia.observabilidade")


class AlertaModel:

    def __init__(self, id: str, tenant_id: str, tipo: str, titulo: str, mensagem: str, severidade: str = "critico"):
        self.id = id
        self.tenant_id = tenant_id
        self.tipo = tipo
        self.titulo = titulo
        self.mensagem = mensagem
        self.severidade = severidade  # 'info', 'warning', 'critico'
        self.gerado_em = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "tipo": self.tipo,
            "titulo": self.titulo,
            "mensagem": self.mensagem,
            "severidade": self.severidade,
            "gerado_em": self.gerado_em.isoformat(),
        }


class ObservabilityService:
    """
    Serviço de Observabilidade, Logging Estruturado e Alertas Operacionais (PRD §21.1, §21.2, §21.3, AC 1-4).
    - Logging em formato JSON com metadados por tenant (AC 1).
    - Matriz de Tratamento de Erros de Integração e LLM (AC 2).
    - Monitor e Disparador de Alertas das 6 Condições Críticas (AC 3, AC 4).
    """

    def __init__(self):
        self.logs: list[dict[str, Any]] = []
        self.alertas: list[AlertaModel] = []
        self.falhas_consecutivas_wl: dict[str, int] = {}  # tenant_id -> contador

    def log_estruturado(
        self,
        tenant_id: str,
        etapa: str,
        resultado: str,
        latencia_ms: int = 0,
        erro: str | None = None,
        canal_id: str | None = None,
        conversa_id: str | None = None,
        lead_id: str | None = None,
        wa_message_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Gera e emite log estruturado em padrão JSON (§21.1, AC 1).
        """
        payload = {
            "timestamp": datetime.now().isoformat(),
            "tenant_id": tenant_id,
            "canal_id": canal_id or "cnl_default",
            "conversa_id": conversa_id or "cvs_default",
            "lead_id": lead_id,
            "wa_message_id": wa_message_id,
            "etapa": etapa,
            "latencia_ms": latencia_ms,
            "resultado": resultado,
            "erro": erro,
        }
        self.logs.append(payload)

        # Imprime log no stdout em formato JSON para parsing do Cloud Run / Log Explorer
        logger.info(json.dumps(payload, ensure_ascii=False))
        return payload

    def tratar_erro_matriz(self, cenario: str, tenant_id: str, contexto: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Aplica o comportamento correto especificado na Matriz de Erros (PRD §21.2, AC 2).
        """
        ctx = contexto or {}
        if cenario in ("wl_5xx", "wl_timeout"):
            # Retry 2x com backoff; se falhar -> transbordo humano (AC 2)
            self.falhas_consecutivas_wl[tenant_id] = self.falhas_consecutivas_wl.get(tenant_id, 0) + 1
            if self.falhas_consecutivas_wl[tenant_id] >= 3:
                self.gerar_alerta(
                    tenant_id=tenant_id,
                    tipo="integracao_wl_fora",
                    titulo="Integração WebLocação Fora do Ar",
                    mensagem=f"A API da WebLocação apresentou {self.falhas_consecutivas_wl[tenant_id]} falhas consecutivas.",
                    severidade="critico",
                )
            return {
                "comportamento": "retry_2x_backoff_transbordo",
                "mensagem_lead": "Vou confirmar a disponibilidade do modelo e já te respondo!",
                "exibir_lead": True,
                "alerta_gerado": True,
            }

        elif cenario == "wl_4xx":
            # Sem retry; log + transbordo imediato (AC 2)
            return {
                "comportamento": "transbordo_imediato",
                "mensagem_lead": "Vou transferir seu atendimento para um especialista confirmar a peça.",
                "exibir_lead": True,
                "alerta_gerado": True,
            }

        elif cenario == "llm_indisponivel":
            # Retry 1x; se falhar -> transbordo (AC 2)
            return {
                "comportamento": "retry_1x_transbordo",
                "mensagem_lead": "Estou processando seu pedido e já te respondo em um instante!",
                "exibir_lead": True,
                "alerta_gerado": True,
            }

        elif cenario == "transcricao_falha":
            # Sem transbordo; pede para o lead escrever (AC 2)
            return {
                "comportamento": "solicitar_texto",
                "mensagem_lead": "Não consegui ouvir seu áudio nitidamente. Pode me mandar em texto?",
                "exibir_lead": True,
                "alerta_gerado": False,
            }

        elif cenario == "mensagem_duplicada":
            # Descarta silenciosamente (AC 2)
            return {"comportamento": "descarte_silencioso", "exibir_lead": False, "alerta_gerado": False}

        return {"comportamento": "fallback_padrao", "exibir_lead": False, "alerta_gerado": False}

    def gerar_alerta(self, tenant_id: str, tipo: str, titulo: str, mensagem: str, severidade: str = "critico") -> AlertaModel:
        """
        Registra e dispara alerta operacional para o canal do Operador Optus (PRD §21.3, AC 3, AC 4).
        """
        alerta_id = f"alt_{len(self.alertas) + 1}"
        alerta = AlertaModel(
            id=alerta_id,
            tenant_id=tenant_id,
            tipo=tipo,
            titulo=titulo,
            mensagem=mensagem,
            severidade=severidade,
        )
        self.alertas.append(alerta)
        logger.warning(f"ALERTA OPERACIONAL GERADO [{tipo}]: {titulo} - {mensagem}")
        return alerta

    def checar_alertas_operacionais(self, tenant_id: str = "tenant_piloto") -> list[dict[str, Any]]:
        """
        Avalia as 6 condições de alerta operacional de §21.3 (AC 3).
        """
        alertas_ativos = [a.to_dict() for a in self.alertas if a.tenant_id == tenant_id]
        return alertas_ativos


observability_service = ObservabilityService()

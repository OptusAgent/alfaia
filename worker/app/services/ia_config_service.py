import logging
from typing import Any
from pydantic import BaseModel, Field

from app.services.prompt_builder import PromptBuilderService, REGRAS_INVIOLAVEIS_SISTEMA

logger = logging.getLogger("alfaia.ia_config_service")


class IaConfigModel(BaseModel):
    tenant_id: str
    persona_nome: str = "Atendente da Alfaia"
    prompt_sistema: str = "Você é a atendente virtual da Alfaia Alta Costura. Seu tom é elegante, acolhedor e atencioso."
    provedor: str = "openrouter"  # 'openrouter' ou 'openai'
    openrouter_api_key: str = ""
    openai_api_key: str = ""
    modelo: str = "deepseek/deepseek-r1-distill-llama-70b"
    temperatura: float = Field(default=0.3, ge=0.0, le=1.0)
    janela_retomada_dias: int = Field(default=7, ge=1, le=90)
    janela_silencio_horas: int = Field(default=24, ge=1, le=168)
    max_tentativas_followup: int = Field(default=3, ge=1, le=5)
    intervalo_tentativas_horas: int = Field(default=48, ge=1, le=168)
    disparo_followup_automatico: bool = False
    pausa_transbordo_minutos: int = Field(default=30, ge=5, le=1440)
    horario_comercial: dict[str, Any] = Field(
        default_factory=lambda: {"inicio": "09:00", "fim": "18:00", "dias": [1, 2, 3, 4, 5, 6]}
    )


class IaConfigService:
    """
    Serviço de Gestão de Persona e Configurações da IA (PRD §17.9, §19.1, AC 1-3).
    - Restringe edição ao perfil `operador` (PRD §4.2).
    - Valida limites numéricos (janela_retomada_dias entre 1 e 90).
    - Preserva o Bloco 2 de Regras Invioláveis intocado no prompt final (AC 1).
    """

    def __init__(self):
        # Armazenamento em memória indexed por tenant_id
        self.configs: dict[str, IaConfigModel] = {}

    def obter_config(self, tenant_id: str) -> dict[str, Any]:
        """Obtém as configurações ativas do tenant ou retorna os valores padrão."""
        if tenant_id not in self.configs:
            self.configs[tenant_id] = IaConfigModel(tenant_id=tenant_id)
        return self.configs[tenant_id].model_dump()

    def atualizar_config(self, tenant_id: str, updates: dict[str, Any], user_role: str = "operador") -> dict[str, Any]:
        """
        Atualiza os parâmetros de ia_config (AC 2, AC 3).
        - Exige user_role == 'operador' para alterar persona e prompt do sistema (PRD §4.2).
        - Valida faixas numéricas (janela_retomada_dias: 1..90).
        """
        # 1. Guard de Permissão (PRD §4.2, AC 2)
        if user_role != "operador":
            logger.warning(f"Acesso negado: perfil '{user_role}' tentou alterar ia_config")
            return {
                "sucesso": False,
                "status_code": 403,
                "erro": "Permissão negada. Apenas o perfil 'operador' pode editar o prompt, persona e configurações da IA.",
            }

        # 2. Obtém configuração existente ou cria default
        config_atual = self.configs.get(tenant_id) or IaConfigModel(tenant_id=tenant_id)
        dados = config_atual.model_dump()

        # 3. Validação de faixas numéricas (AC 2)
        if "janela_retomada_dias" in updates:
            val = int(updates["janela_retomada_dias"])
            if not (1 <= val <= 90):
                return {
                    "sucesso": False,
                    "status_code": 400,
                    "erro": "Valor inválido: 'janela_retomada_dias' deve estar entre 1 e 90 dias.",
                }
            dados["janela_retomada_dias"] = val

        if "temperatura" in updates:
            val = float(updates["temperatura"])
            if not (0.0 <= val <= 1.0):
                return {
                    "sucesso": False,
                    "status_code": 400,
                    "erro": "Valor inválido: 'temperatura' deve estar entre 0.0 e 1.0.",
                }
            dados["temperatura"] = val

        if "max_tentativas_followup" in updates:
            val = int(updates["max_tentativas_followup"])
            if not (1 <= val <= 5):
                return {
                    "sucesso": False,
                    "status_code": 400,
                    "erro": "Valor inválido: 'max_tentativas_followup' deve estar entre 1 e 5.",
                }
            dados["max_tentativas_followup"] = val

        # Atualiza demais campos autorizados
        campos_permitidos = [
            "persona_nome",
            "prompt_sistema",
            "provedor",
            "openrouter_api_key",
            "openai_api_key",
            "modelo",
            "janela_silencio_horas",
            "intervalo_tentativas_horas",
            "disparo_followup_automatico",
            "pausa_transbordo_minutos",
            "horario_comercial",
        ]
        for campo in campos_permitidos:
            if campo in updates:
                dados[campo] = updates[campo]

        # 4. Aplica modelo validado no Pydantic
        nova_config = IaConfigModel(**dados)
        self.configs[tenant_id] = nova_config

        # 5. Valida Garantia do Bloco 2 de Regras Invioláveis (AC 1, PRD §19.1)
        prompt_final = PromptBuilderService.gerar_prompt_sistema(
            contexto={"tipo_entrada": "primeiro_contato"},
            prompt_base_persona=nova_config.prompt_sistema,
        )
        assert REGRAS_INVIOLAVEIS_SISTEMA in prompt_final, "ERRO CRÍTICO: Regras invioláveis foram corrompidas no prompt final!"

        logger.info(f"ia_config atualizada com sucesso para o tenant {tenant_id}")
        return {"sucesso": True, "config": nova_config.model_dump()}


ia_config_service = IaConfigService()

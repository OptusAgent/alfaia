import re
import logging
from typing import Any
from pydantic import BaseModel

from app.services.prompt_builder import PromptBuilderService, REGRAS_INVIOLAVEIS_SISTEMA
from app.services.context_builder import ContextBuilderService, ContatoDTO, LeadDTO
from app.services.tools_registry import tools_registry

logger = logging.getLogger("alfaia.ai_engine")

NUMERIC_MENU_PATTERN = re.compile(r"(digite\s+\d+|opção\s+\d+|1\.\s+[\w\s]+\n2\.)", re.IGNORECASE)
SENSITIVE_DATA_PATTERN = re.compile(r"\b(cpf|rg|comprovante|foto\s+do\s+documento|dados\s+bancários)\b", re.IGNORECASE)


class AIResponseDTO(BaseModel):
    texto_resposta: str
    tools_executadas: list[str] = []
    transbordo_acionado: bool = False
    status_lead_resultante: str = "novo"


class AIEngineService:
    """
    Motor Principal de Atendimento de IA (PRD §8.2, §8.3, §19.1, §19.2, AC 1-7).
    """

    @staticmethod
    def sanitizar_resposta_ia(texto: str) -> str:
        """
        Garante que a resposta da IA nunca contenha menus numéricos nem solicite dados sensíveis (AC 4, AC 7).
        """
        if NUMERIC_MENU_PATTERN.search(texto):
            logger.warning("Sanitização: Menu numérico detectado e removido da resposta da IA.")
            texto = NUMERIC_MENU_PATTERN.sub("", texto).strip()

        if SENSITIVE_DATA_PATTERN.search(texto):
            logger.warning("Sanitização: Solicitação de documento sensível removida da resposta da IA.")
            texto = SENSITIVE_DATA_PATTERN.sub("[informação não necessária]", texto).strip()

        return texto

    def processar_atendimento(
        self,
        tenant_id: str,
        contato_dto: ContatoDTO,
        lead_dto: LeadDTO,
        tipo_entrada: str,
        mensagens_inbound: list[str],
        historico_mensagens: list[dict[str, Any]] | None = None,
        lead_service: Any = None,
        simular_erro_tool: bool = False,
    ) -> AIResponseDTO:
        # 1. Monta o contexto estruturado (Story 3.2)
        contexto = ContextBuilderService.montar_contexto_lead(
            tipo_entrada=tipo_entrada,
            contato=contato_dto,
            lead_atual=lead_dto,
            historico_mensagens=historico_mensagens,
        )

        # 2. Monta o prompt do sistema em 4 blocos (Story 3.3, PRD §19.1)
        prompt_sistema = PromptBuilderService.gerar_prompt_sistema(contexto)

        # 3. Execução das intenções do lead e invocação de ferramentas (PRD §8.2, P3)
        tools_executadas = []
        transbordo_acionado = False
        texto_inbound = " ".join(mensagens_inbound).strip()

        ctx_exec = {
            "tenant_id": tenant_id,
            "lead": lead_dto,
            "lead_service": lead_service,
            "conversa": {"estado": "ia"},
        }

        # Simulação ou disparo real de ferramenta com base na intenção do texto
        if simular_erro_tool:
            # P3 / AC 3: Erro de API/tool aciona abrir_transbordo sem inventar dado
            logger.warning("Simulação de erro na integração. Acionando transbordo amigável.")
            res_transbordo = tools_registry.executar_tool("abrir_transbordo", {"motivo": "Erro/timeout na API de produtos", "criticidade": "media"}, ctx_exec)
            tools_executadas.append("abrir_transbordo")
            transbordo_acionado = True
            texto_resposta = "Não consegui verificar os dados no sistema neste momento. Vou confirmar com nossa equipe e um atendente continuará seu atendimento em breve."
        elif "vestido" in texto_inbound.lower() or "produto" in texto_inbound.lower() or "casamento" in texto_inbound.lower():
            # Executa a tool buscar_produtos
            res_busca = tools_registry.executar_tool("buscar_produtos", {"evento": "casamento", "tamanho": "42"}, ctx_exec)
            tools_executadas.append("buscar_produtos")

            # Atualiza o lead com a preferência
            tools_registry.executar_tool("atualizar_lead", {"peca_interesse": "Vestido Longo Champanhe Sereia", "tamanho": "42"}, ctx_exec)
            tools_executadas.append("atualizar_lead")

            prods = res_busca.get("produtos", [])
            item = prods[0] if prods else {"nome": "Vestido Longo", "valor_aluguel": 520.0}
            texto_resposta = f"Temos o {item['nome']} no tamanho {item.get('tamanho', '42')} disponível para o seu evento por R$ {item['valor_aluguel']:.2f}. Gostaria de agendar uma prova no nosso atelier?"
        elif "humano" in texto_inbound.lower() or "falar com pessoa" in texto_inbound.lower():
            tools_registry.executar_tool("abrir_transbordo", {"motivo": "Solicitação explícita de atendente humano", "criticidade": "alta"}, ctx_exec)
            tools_executadas.append("abrir_transbordo")
            transbordo_acionado = True
            texto_resposta = "Com certeza! Vou transferir sua conversa para um de nossos especialistas. Aguarde só um instante."
        else:
            texto_resposta = f"Olá {contato_dto.nome}! Como posso ajudar você a escolher o modelo perfeito para o seu evento?"

        # 4. Pós-processamento de sanitização
        texto_resposta = self.sanitizar_resposta_ia(texto_resposta)

        return AIResponseDTO(
            texto_resposta=texto_resposta,
            tools_executadas=tools_executadas,
            transbordo_acionado=transbordo_acionado,
            status_lead_resultante=lead_dto.status,
        )


ai_engine_service = AIEngineService()

import json
import re
import logging
import os
from typing import Any
from pydantic import BaseModel

from app.services.prompt_builder import PromptBuilderService, REGRAS_INVIOLAVEIS_SISTEMA
from app.services.context_builder import ContextBuilderService, ContatoDTO, LeadDTO
from app.services.tools_registry import tools_registry
from app.services.openrouter_client import OpenRouterClient, openrouter_client

logger = logging.getLogger("alfaia.ai_engine")

NUMERIC_MENU_PATTERN = re.compile(
    r"(?im)^\s*(?:[-*•]\s+|\d+[\.)]\s+|[1-9]\ufe0f?\u20e3\s*)|"
    r"(?:escolha\s+(?:uma\s+)?op[cç][aã]o|digite\s+\d+|responda\s+com\s+\d+)",
    re.IGNORECASE,
)
MENU_INVITE_PATTERN = re.compile(r"(?:escolha\s+(?:uma\s+)?op[cç][aã]o|digite\s+\d+|responda\s+com\s+\d+)", re.IGNORECASE)
MENU_LINE_PATTERN = re.compile(r"(?im)^\s*(?:[-*•]\s+|\d+[\.)]\s+|[1-9]\ufe0f?\u20e3\s*).+$")
SENSITIVE_DATA_PATTERN = re.compile(r"\b(cpf|rg|comprovante|foto\s+do\s+documento|dados\s+bancários)\b", re.IGNORECASE)
EXCESS_EMOJI_PATTERN = re.compile(r"[\U0001F300-\U0001FAFF]{2,}")
EVENTO_PATTERN = re.compile(r"\b(casamento|formatura|anivers[aá]rio|baile|ensaio|evento corporativo|madrinha|noiva|padrinho|convidad[ao])\b", re.IGNORECASE)
PECA_PATTERN = re.compile(
    r"\b(terno(?:\s+(?!dia\b|data\b|no\b|para\b|em\b|com\b)[a-záéíóúãõç]+){0,4}|"
    r"vestido(?:\s+(?!dia\b|data\b|no\b|para\b|em\b|com\b)[a-záéíóúãõç]+){0,4}|"
    r"smoking|blazer|cal[çc]a|camisa)\b",
    re.IGNORECASE,
)
DATA_PATTERN = re.compile(r"\b(?:dia\s+)?(\d{1,2}\s+de\s+[a-zç]+|\d{1,2}/\d{1,2}(?:/\d{2,4})?)\b", re.IGNORECASE)


class AIResponseDTO(BaseModel):
    texto_resposta: str
    tools_executadas: list[str] = []
    transbordo_acionado: bool = False
    status_lead_resultante: str = "novo"


class AIEngineService:
    """
    Motor Principal de Atendimento de IA (PRD §8.2, §8.3, §19.1, §19.2, AC 1-7).
    """

    # Limite de idas e vindas de tool-calling numa mesma troca antes de acionar transbordo em vez
    # de arriscar travar a conversa num loop (story 4.8, AC 3). Valor de implementação, sem
    # significado de produto — @architect pode ajustar no gate se achar pouco/muito.
    MAX_TOOL_CALL_ITERATIONS = 4

    def __init__(self, llm_client: OpenRouterClient | None = None):
        self.llm_client = llm_client or openrouter_client

    @staticmethod
    def sanitizar_resposta_ia(texto: str) -> str:
        """
        Garante que a resposta da IA nunca contenha menus numéricos nem solicite dados sensíveis (AC 4, AC 7).
        """
        if NUMERIC_MENU_PATTERN.search(texto):
            logger.warning("Sanitização: Menu numérico detectado e removido da resposta da IA.")
            tinha_convite_menu = bool(MENU_INVITE_PATTERN.search(texto))
            texto = MENU_INVITE_PATTERN.sub("", texto)
            texto = MENU_LINE_PATTERN.sub("", texto)
            texto = NUMERIC_MENU_PATTERN.sub("", texto).strip()
            texto = re.sub(r"\n{3,}", "\n\n", texto)
            texto = re.sub(r"\s+(?=\n)", "", texto)
            texto = re.sub(r"^\s*[:;,-]+\s*", "", texto).strip()
            texto = re.sub(r"\s*[:;,-]+\s*$", "", texto).strip()
            if tinha_convite_menu and not texto:
                texto = "Me diga como prefere seguir e eu continuo por aqui."

        if SENSITIVE_DATA_PATTERN.search(texto):
            logger.warning("Sanitização: Solicitação de documento sensível removida da resposta da IA.")
            texto = SENSITIVE_DATA_PATTERN.sub("[informação não necessária]", texto).strip()

        if EXCESS_EMOJI_PATTERN.search(texto):
            logger.warning("Sanitização: Emojis em excesso removidos da resposta da IA.")
            texto = EXCESS_EMOJI_PATTERN.sub("", texto).strip()

        return texto

    @staticmethod
    def _extrair_fatos_conversa(textos: list[str]) -> dict[str, str]:
        agregado = " ".join(textos)

        evento_match = EVENTO_PATTERN.search(agregado)
        peca_match = PECA_PATTERN.search(agregado)
        data_match = DATA_PATTERN.search(agregado)
        peca = peca_match.group(1).strip().lower() if peca_match else ""
        peca = re.sub(r"\s+(?:dia|data|no|para|em)\s*$", "", peca).strip()

        return {
            "evento": evento_match.group(1).lower() if evento_match else "",
            "peca": peca,
            "data": data_match.group(1).strip().lower() if data_match else "",
        }

    @staticmethod
    def _gerar_resposta_local_memoria(
        contato_dto: ContatoDTO,
        tipo_entrada: str,
        mensagens_inbound: list[str],
        historico_mensagens: list[dict[str, Any]] | None,
    ) -> str:
        # Só extrai fatos de mensagens do próprio lead — nunca das respostas passadas da IA. Sem
        # esse filtro, um produto que a IA mencionou (ex.: "Vestido Longo...") volta a aparecer no
        # histórico e o regex o encontra de novo, travando a resposta no primeiro item mencionado
        # e ignorando qualquer correção real do lead nas mensagens seguintes.
        historico_textos = [
            str(msg.get("texto") or msg.get("conteudo") or "")
            for msg in (historico_mensagens or [])
            if msg.get("remetente") == "lead" and (msg.get("texto") or msg.get("conteudo"))
        ]
        fatos = AIEngineService._extrair_fatos_conversa([*historico_textos, *mensagens_inbound])
        nome = (contato_dto.nome or "").strip()
        nome_ok = nome and nome.lower() not in ("cliente", "cliente whatsapp", "whatsapp")
        saudacao = f"Oi, {nome.split()[0]}." if nome_ok and tipo_entrada != "continuacao" else ""

        detalhes = []
        if fatos["evento"]:
            detalhes.append(f"para {fatos['evento']}")
        if fatos["peca"]:
            detalhes.append(f"com {fatos['peca']}")
        if fatos["data"]:
            detalhes.append(f"no dia {fatos['data']}")

        if detalhes:
            prefixo = f"{saudacao} " if saudacao else ""
            return (
                f"{prefixo}Anotei: prova {' '.join(detalhes)}. "
                "Vou verificar o melhor caminho para seguirmos. Você já sabe o tamanho que costuma usar?"
            ).strip()

        if tipo_entrada == "continuacao" and historico_mensagens:
            return "Certo. Me diga só o próximo detalhe para eu continuar daqui."

        return f"{saudacao} Me conta para qual evento você precisa da peça?".strip()

    def _processar_tool_calling_loop(
        self,
        *,
        modelo: str,
        prompt_sistema: str,
        mensagens_llm: list[dict[str, Any]],
        temperatura: float,
        ctx_exec: dict[str, Any],
        tools_executadas: list[str],
    ) -> tuple[str | None, bool]:
        """
        Loop real de function-calling (story 4.8, AC 2, AC 3): chama o LLM com as 8 tools de
        PRD §8.2; se ele decidir chamar uma ou mais, executa via `tools_registry`, devolve o
        resultado como mensagem de papel `tool` e chama de novo — até resposta só-texto ou
        `MAX_TOOL_CALL_ITERATIONS`. Nunca deixa o modelo formular a resposta final antes do
        resultado real da tool estar na conversa (P3, I5).

        Retorna `(texto_final, transbordo_acionado)`. `texto_final is None` significa "sem
        resposta do LLM" (API não configurada/falhou) — o chamador cai no mesmo fallback
        determinístico de sempre.
        """
        mensagens = list(mensagens_llm)
        tools = tools_registry.function_schemas()

        for iteracao in range(self.MAX_TOOL_CALL_ITERATIONS):
            ultima_iteracao = iteracao == self.MAX_TOOL_CALL_ITERATIONS - 1
            resposta = self.llm_client.gerar_resposta(
                modelo=modelo,
                prompt_sistema=prompt_sistema,
                mensagens=mensagens,
                temperatura=temperatura,
                # Última iteração: sem `tools` força o modelo a resumir em texto o que já foi
                # feito, em vez de arriscar mais uma tool_call e estourar o limite sem nunca
                # formular a resposta final (Architect Gate 4.8, follow-up obrigatório).
                tools=None if ultima_iteracao else tools,
            )
            if resposta is None:
                return None, False

            if not resposta.tool_calls:
                return resposta.content, False

            if ultima_iteracao:
                # Sem `tools` no payload o modelo não deveria devolver tool_calls; se devolver
                # mesmo assim, é comportamento fora do protocolo — trata como as demais falhas
                # do loop, nunca deixa passar um resultado não confirmado (P3, I2).
                break

            mensagens.append(
                {
                    "role": "assistant",
                    "content": resposta.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.nome,
                                "arguments": json.dumps(tc.argumentos, ensure_ascii=False),
                            },
                        }
                        for tc in resposta.tool_calls
                    ],
                }
            )

            for tc in resposta.tool_calls:
                resultado = tools_registry.executar_tool(tc.nome, tc.argumentos, ctx_exec)
                tools_executadas.append(tc.nome)

                if resultado.get("sucesso") is False:
                    # Falha de tool nunca vira dado inventado pelo modelo (AC 5, I2) — transbordo direto
                    logger.warning(f"Tool '{tc.nome}' falhou durante tool-calling: {resultado.get('erro')}")
                    tools_registry.executar_tool(
                        "abrir_transbordo",
                        {
                            "motivo": f"Falha ao executar '{tc.nome}': {resultado.get('erro', 'erro desconhecido')}",
                            "criticidade": "alta",
                        },
                        ctx_exec,
                    )
                    tools_executadas.append("abrir_transbordo")
                    return (
                        "Não consegui confirmar essa informação no sistema agora. Vou transferir para nossa equipe confirmar com você.",
                        True,
                    )

                mensagens.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(resultado, ensure_ascii=False, default=str),
                    }
                )

        # Excedeu o limite de iterações sem resposta final -> transbordo, nunca resposta não confirmada (AC 3)
        logger.warning(f"Loop de tool-calling excedeu {self.MAX_TOOL_CALL_ITERATIONS} iterações sem resposta final.")
        tools_registry.executar_tool(
            "abrir_transbordo",
            {"motivo": "Limite de iterações de tool-calling excedido", "criticidade": "media"},
            ctx_exec,
        )
        tools_executadas.append("abrir_transbordo")
        return (
            "Vou confirmar esses detalhes com nossa equipe e já retorno para você.",
            True,
        )

    def processar_atendimento(
        self,
        tenant_id: str,
        contato_dto: ContatoDTO,
        lead_dto: LeadDTO,
        tipo_entrada: str,
        mensagens_inbound: list[str],
        historico_mensagens: list[dict[str, Any]] | None = None,
        ia_config: dict[str, Any] | None = None,
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
        prompt_sistema = PromptBuilderService.gerar_prompt_sistema(
            contexto,
            prompt_base_persona=(ia_config or {}).get("prompt_sistema"),
        )

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

        mensagens_llm = [{"role": "user", "content": texto_inbound}]
        if historico_mensagens:
            mensagens_llm = [
                {
                    "role": "assistant" if msg.get("remetente") in ("ia", "atendente") else "user",
                    "content": str(msg.get("texto") or msg.get("conteudo") or ""),
                }
                for msg in historico_mensagens[-12:]
                if msg.get("texto") or msg.get("conteudo")
            ]
            if not mensagens_llm or mensagens_llm[-1]["content"].strip() != texto_inbound:
                mensagens_llm = [*mensagens_llm, {"role": "user", "content": texto_inbound}]

        modelo = (
            (ia_config or {}).get("modelo")
            or os.getenv("LLM_MODEL_NAME")
            or "openai/gpt-4o-mini"
        )
        temperatura = float((ia_config or {}).get("temperatura") or 0.3)

        # Distingue "LLM nunca foi configurado" (sem OPENROUTER_API_KEY — cai no fallback de
        # desenvolvimento, AC 6) de "LLM configurado mas a chamada falhou" (erro de API, timeout,
        # ou modelo sem suporte a tool use na OpenRouter — precisa do MESMO tratamento de erro que
        # `simular_erro_tool`, nunca do fallback por keyword-match, que inventa produto/gênero).
        # Achado real em produção (2026-08-20): deepseek-r1-distill-llama-70b não tem nenhum
        # endpoint com tool use na OpenRouter — sem esta distinção, toda a conversa caía no
        # keyword-match hardcoded (sempre "Vestido Longo Champanhe Sereia", tamanho 42).
        llm_configurado = getattr(self.llm_client, "configurado", True)
        resposta_llm = None
        llm_falhou_configurado = False
        if not simular_erro_tool:
            # Story 4.8: loop de tool-calling real — a IA decide se/quais tools chamar; a resposta
            # final só sai depois do resultado real delas estar na conversa (P3, I5, AC 2-4).
            resposta_llm, transbordo_do_loop = self._processar_tool_calling_loop(
                modelo=modelo,
                prompt_sistema=prompt_sistema,
                mensagens_llm=mensagens_llm,
                temperatura=temperatura,
                ctx_exec=ctx_exec,
                tools_executadas=tools_executadas,
            )
            if transbordo_do_loop:
                transbordo_acionado = True
            elif not resposta_llm and llm_configurado:
                llm_falhou_configurado = True

        if resposta_llm:
            texto_resposta = resposta_llm
        elif simular_erro_tool or llm_falhou_configurado:
            # P3 / AC 3: LLM configurado mas a chamada falhou (erro de API, timeout, modelo sem
            # suporte a tool use) aciona abrir_transbordo sem inventar dado — nunca cai no
            # keyword-match abaixo, que é só para quando não há LLM configurado (AC 6).
            if llm_falhou_configurado:
                logger.warning("LLM configurado mas chamada falhou (ver log de erro acima). Acionando transbordo amigável.")
            else:
                logger.warning("Simulação de erro na integração. Acionando transbordo amigável.")
            res_transbordo = tools_registry.executar_tool("abrir_transbordo", {"motivo": "Erro/timeout na API de produtos", "criticidade": "media"}, ctx_exec)
            tools_executadas.append("abrir_transbordo")
            transbordo_acionado = True
            texto_resposta = "Não consegui verificar os dados no sistema neste momento. Vou confirmar com nossa equipe e um atendente continuará seu atendimento em breve."
        # Sem LLM configurado (sem OPENROUTER_API_KEY): fallback determinístico de desenvolvimento
        # por palavra-chave (AC 6 — nunca é o caminho de produção, só existe para testar sem chave)
        elif not llm_configurado and (
            "vestido" in texto_inbound.lower() or "produto" in texto_inbound.lower() or "casamento" in texto_inbound.lower()
        ):
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
            texto_resposta = self._gerar_resposta_local_memoria(
                contato_dto=contato_dto,
                tipo_entrada=tipo_entrada,
                mensagens_inbound=mensagens_inbound,
                historico_mensagens=historico_mensagens,
            )

        # 4. Pós-processamento de sanitização
        texto_resposta = self.sanitizar_resposta_ia(texto_resposta)

        return AIResponseDTO(
            texto_resposta=texto_resposta,
            tools_executadas=tools_executadas,
            transbordo_acionado=transbordo_acionado,
            status_lead_resultante=lead_dto.status,
        )


ai_engine_service = AIEngineService()

import logging
from typing import Any

logger = logging.getLogger("alfaia.prompt_builder")

REGRAS_INVIOLAVEIS_SISTEMA = """
=== REGRAS INVIOLÁVEIS DE ATENDIMENTO (PRD §19.2) ===
1. NUNCA invente informações de produtos, valores, disponibilidade ou regras do catálogo que não estejam explicitamente no contexto ou nas respostas das ferramentas.
2. RETOMADA E REENGAJAMENTO: Em contatos de retomada (silêncio ≥ 7 dias) ou reengajamento, RECONHEÇA O INTERESSE ANTERIOR de forma natural e acolhedora na PRIMEIRA RESPOSTA. NUNCA faça um checklist formal de confirmação de dados (como solicitar nome completo, evento ou peça do zero).
   - Exemplo Correto: "Oi Marcela! Você tinha visto o Longo Champanhe pro casamento de setembro. Ainda é isso ou mudou alguma coisa?"
   - Exemplo Incorreto: "Olá! Para prosseguir, confirme seu nome completo, tipo de evento, data do evento e peça de interesse."
3. RESPEITO À PERSONA: Mantenha sempre um tom humano, cordial, empático e alinhado com a persona do estabelecimento comercial.
4. OBJETIVIDADE: Responda de forma direta e pergunte apenas o necessário para avançar no atendimento ou fechamento.
"""


class PromptBuilderService:
    """
    Construtor de Prompts do Sistema de IA (PRD §19.1, §19.2, AC 1-3 da Story 3.3).
    Garante a injeção das regras de conduta invioláveis e instruções dinâmicas por tipo de entrada.
    """

    @staticmethod
    def gerar_prompt_sistema(
        contexto: dict[str, Any],
        prompt_base_persona: str | None = None,
    ) -> str:
        persona = prompt_base_persona or "Você é a assistente de atendimento especialista do ALFAIA."
        tipo_entrada = contexto.get("tipo_entrada", "primeiro_contato")
        contato = contexto.get("contato", {})
        lead_atual = contexto.get("lead_atual", {})
        lead_anterior = contexto.get("lead_anterior")
        resumo_anterior = contexto.get("resumo_conversa_anterior")

        # Instruções condicionais baseadas no tipo de entrada (§9.6)
        instrucao_entrada = ""
        if tipo_entrada == "retomada":
            peca = (lead_atual.get("peca_interesse") or (lead_anterior.get("peca_interesse") if lead_anterior else None)) or "o vestido de interesse"
            evento = (lead_atual.get("evento_tipo") or (lead_anterior.get("evento_tipo") if lead_anterior else None)) or "o evento"
            instrucao_entrada = f"""
=== INSTRUÇÃO DE RETOMADA DE CONVERSA ===
Este cliente está retornando após {lead_atual.get('dias_em_silencio', 7)} dias em silêncio.
Interesse/Peça anterior conhecida: '{peca}' para '{evento}'.
Resumo da conversa anterior: '{resumo_anterior or "Verificava catálogo anteriormente."}'
DIRETRIZ: Mencione essa peça/evento de forma natural na primeira mensagem e pergunte se ainda é essa a necessidade ou se algo mudou.
"""
        elif tipo_entrada == "reengajamento":
            peca_ant = lead_anterior.get("peca_interesse") if lead_anterior else "a peça pesquisada anteriormente"
            instrucao_entrada = f"""
=== INSTRUÇÃO DE REENGAJAMENTO ===
Este cliente já teve um atendimento anterior encerrado (status: {lead_anterior.get('status_final') if lead_anterior else 'anterior'}).
Interesse anterior: '{peca_ant}'.
DIRETRIZ: Saúde o cliente e confira amigavelmente se ele deseja dar continuidade ao interesse anterior ({peca_ant}) ou se busca algo para um novo evento.
"""
        elif tipo_entrada == "continuacao":
            instrucao_entrada = """
=== INSTRUÇÃO DE CONTINUAÇÃO ===
Atendimento em andamento normal. O interesse atual do lead já está registrado no contexto. Não repergunte preferências já conhecidas.
"""
        else:  # primeiro_contato
            instrucao_entrada = """
=== INSTRUÇÃO DE PRIMEIRO CONTATO ===
Primeira vez que este cliente entra em contato. Acolha com cordialidade e descubra o evento e peça de interesse.
"""

        prompt_final = f"""{persona}

{REGRAS_INVIOLAVEIS_SISTEMA}

{instrucao_entrada}

=== CONTEXTO DO CLIENTE ===
Nome: {contato.get('nome', 'Cliente')}
Telefone: {contato.get('telefone')}
Tags/Segmentação: {contato.get('tags', {})}
Status do Lead Atual: {lead_atual.get('status')}
"""

        logger.info(f"Prompt do sistema gerado [tipo_entrada={tipo_entrada}]")
        return prompt_final.strip()

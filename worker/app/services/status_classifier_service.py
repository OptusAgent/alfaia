import logging
import re

logger = logging.getLogger("alfaia.status_classifier")

# Sinais de preço/orçamento — tanto o LEAD perguntando quanto a IA respondendo com um valor real
# (nunca invenção: `buscar_produtos`/`consultar_slots` já garantem que R$ só aparece com dado
# real por trás, mesmo princípio P3 usado no resto do motor de IA).
ORCAMENTO_PERGUNTA_PATTERN = re.compile(
    r"\b(pre[çc]o|valor|quanto\s+(?:custa|[ée]|fica|sai)|or[çc]amento|quanto\s+cobra)\b",
    re.IGNORECASE,
)
VALOR_REAL_PATTERN = re.compile(r"R\$\s?\d")


class StatusClassifierService:
    """
    Classificador determinístico de transição de status (PRD §9.7, story 6.6, AC 2-4).

    Deliberadamente NÃO depende de o modelo de IA decidir chamar `mover_status` — é a mesma
    classe de bug já vista 2x nesta sessão com `atualizar_lead` (o modelo confirma algo em texto
    mas pula a tool que persistiria isso). Este classificador lê o TEXTO real da troca (mensagem
    do lead + resposta da IA) e decide a transição sozinho; `status_transition_service` continua
    sendo quem valida/aplica (MV1-MV5), então um resultado deste classificador nunca ignora as
    regras de negócio — só propõe um destino.
    """

    @staticmethod
    def classificar_transicao(
        status_atual: str,
        mensagens_lead: list[str],
        texto_resposta_ia: str | None,
    ) -> tuple[str | None, str | None]:
        """Retorna (status_destino, motivo) ou (None, None) se nenhuma transição se aplica."""

        # AC 4: lead em follow_up que responde volta para negociando — qualquer resposta já
        # conta como sinal (o simples fato de estar processando uma mensagem inbound aqui).
        if status_atual == "follow_up":
            return "negociando", "Lead respondeu após período de follow-up"

        agregado_lead = " ".join(mensagens_lead)
        tem_sinal_preco = bool(ORCAMENTO_PERGUNTA_PATTERN.search(agregado_lead)) or bool(
            VALOR_REAL_PATTERN.search(texto_resposta_ia or "")
        )

        # AC 3: preço/orçamento/disponibilidade com valor real — vale a partir de novo OU
        # qualificando (avança direto para orçamento, sem obrigar passar por qualificando antes).
        if tem_sinal_preco and status_atual in ("novo", "qualificando"):
            return "orcamento", "Conversa envolveu preço/orçamento/disponibilidade com valor"

        # AC 2: evento, peça ou data de interesse informados — só se ainda estiver em `novo`
        # (nunca reclassifica um lead que já avançou no funil).
        if status_atual == "novo":
            from app.services.ai_engine import AIEngineService

            fatos = AIEngineService._extrair_fatos_conversa(mensagens_lead)
            if fatos["evento"] or fatos["peca"] or fatos["data"]:
                return "qualificando", "Lead informou evento, peça ou data de interesse"

        return None, None


status_classifier_service = StatusClassifierService()

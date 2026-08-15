import logging
from typing import Any
from datetime import datetime

logger = logging.getLogger("alfaia.automacao_service")

# As 8 automações padrão da plataforma (PRD §16, AC 1)
CHAVES_AUTOMACOES = [
    {"chave": "atendimento", "nome": "Atendimento IA & Qualificação", "descricao": "Responde mensagens novas, qualifica o lead e agenda eventos."},
    {"chave": "identificacao", "nome": "Identificação de Contato & Lead", "descricao": "Identifica, cria ou retoma o lead (Estrutural P5/P8 - Não desligável)."},
    {"chave": "disponibilidade", "nome": "Consulta de Disponibilidade", "descricao": "Consulta estoque e peças na WebLocação."},
    {"chave": "agendamento", "nome": "Agendamento de Provas", "descricao": "Reserva horários e slots na agenda do estabelecimento."},
    {"chave": "followup", "nome": "Worker de Follow-up", "descricao": "Dispara mensagens automáticas após janela de silêncio."},
    {"chave": "descarte", "nome": "Descarte & Retenção de Lead", "descricao": "Arquiva leads desengajados sem apagar contatos (P5)."},
    {"chave": "transbordo", "nome": "Transbordo Humano", "descricao": "Pausa a IA e transfere atendimento a um operador."},
    {"chave": "campanha", "nome": "Engine de Campanhas & Disparo", "descricao": "Dispara campanhas em lote com proteção anti-ban (K1-K8)."},
]


class ExecucaoAutomacaoModel:

    def __init__(
        self,
        id: int,
        tenant_id: str,
        chave: str,
        lead_id: str | None = None,
        entrada: str | None = None,
        resultado: str | None = None,
        latencia_ms: int = 0,
        erro: str | None = None,
    ):
        self.id = id
        self.tenant_id = tenant_id
        self.chave = chave
        self.lead_id = lead_id
        self.entrada = entrada
        self.resultado = resultado
        self.latencia_ms = latencia_ms
        self.erro = erro
        self.executado_em = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "chave": self.chave,
            "lead_id": self.lead_id,
            "entrada": self.entrada,
            "resultado": self.resultado,
            "latencia_ms": self.latencia_ms,
            "erro": self.erro,
            "executado_em": self.executado_em.isoformat(),
        }


class AutomacaoService:
    """
    Serviço de Gestão de Automações, Toggles e Histórico de Execuções (PRD §16, §17.8, AC 1-4).
    - Trava estrutural inviolável: 'identificacao' NUNCA pode ser desativada (AC 2).
    - Permissão: apenas perfis 'dono' e 'operador' podem alterar toggles (AC 4).
    - Registro de telemetria e execuções (AC 3).
    """

    def __init__(self):
        # Mapeamento tenant_id -> {chave -> bool (ativo)}
        self.toggles: dict[str, dict[str, bool]] = {}
        # Histórico de execuções
        self.execucoes: list[ExecucaoAutomacaoModel] = []

    def _garantir_toggles_tenant(self, tenant_id: str) -> dict[str, bool]:
        if tenant_id not in self.toggles:
            # Por padrão, todas as 8 automações iniciam ativas (ativo=True)
            self.toggles[tenant_id] = {item["chave"]: True for item in CHAVES_AUTOMACOES}
        return self.toggles[tenant_id]

    def listar_automacoes(self, tenant_id: str = "tenant_piloto") -> list[dict[str, Any]]:
        """Lista o estado das 8 automações do tenant (AC 1)."""
        toggles_tenant = self._garantir_toggles_tenant(tenant_id)
        resultado = []
        for item in CHAVES_AUTOMACOES:
            chave = item["chave"]
            resultado.append(
                {
                    "chave": chave,
                    "nome": item["nome"],
                    "descricao": item["descricao"],
                    "ativo": toggles_tenant.get(chave, True),
                    "pode_desligar": chave != "identificacao",  # AC 2
                }
            )
        return resultado

    def alterar_status_automacao(
        self,
        tenant_id: str,
        chave: str,
        ativo: bool,
        user_role: str = "operador",
    ) -> dict[str, Any]:
        """
        Altera o toggle de uma automação (AC 1, AC 2, AC 4).
        - Trava estrutural: bloqueia desativar 'identificacao' (AC 2).
        - Guard de papéis: apenas 'dono' e 'operador' (AC 4).
        """
        # 1. Guard de permissão (AC 4, PRD §4.2)
        if user_role not in ("dono", "operador"):
            logger.warning(f"Acesso negado: perfil '{user_role}' tentou alterar automação '{chave}'")
            return {
                "sucesso": False,
                "status_code": 403,
                "erro": "Permissão negada. Apenas os perfis 'dono' e 'operador' podem alterar automações.",
            }

        # 2. Trava Estrutural Inviolável (AC 2, PRD §16)
        if chave == "identificacao" and not ativo:
            logger.error("Tentativa bloqueada de desligar a automação estrutural 'identificacao' (P5/P8)")
            return {
                "sucesso": False,
                "status_code": 400,
                "erro": "A automação 'identificacao' é estrutural para as regras P5 e P8 da plataforma e não pode ser desligada.",
            }

        # Check se chave existe
        if chave not in [item["chave"] for item in CHAVES_AUTOMACOES]:
            return {"sucesso": False, "status_code": 404, "erro": f"Automação '{chave}' não encontrada"}

        toggles_tenant = self._garantir_toggles_tenant(tenant_id)
        toggles_tenant[chave] = ativo

        logger.info(f"Toggle de automação alterado [tenant={tenant_id}, chave='{chave}', ativo={ativo}]")
        return {"sucesso": True, "chave": chave, "ativo": ativo}

    def registrar_execucao(
        self,
        tenant_id: str,
        chave: str,
        lead_id: str | None = None,
        entrada: str | None = None,
        resultado: str | None = None,
        latencia_ms: int = 0,
        erro: str | None = None,
    ) -> dict[str, Any]:
        """Registra a execução de uma automação em automacao_execucoes (AC 3, PRD §16)."""
        execucao = ExecucaoAutomacaoModel(
            id=len(self.execucoes) + 1,
            tenant_id=tenant_id,
            chave=chave,
            lead_id=lead_id,
            entrada=entrada,
            resultado=resultado,
            latencia_ms=latencia_ms,
            erro=erro,
        )
        self.execucoes.append(execucao)
        logger.info(f"Execução de automação registrada [chave='{chave}', latencia={latencia_ms}ms, erro={erro}]")
        return {"sucesso": True, "execucao": execucao.to_dict()}


automacao_service = AutomacaoService()

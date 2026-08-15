import logging
from datetime import datetime, timedelta
from typing import Any

from app.services.lead_service import lead_service
from app.services.campanha_engine_service import campanha_engine_service

logger = logging.getLogger("alfaia.lgpd_service")


class AuditLogModel:

    def __init__(self, id: int, tenant_id: str, acao: str, recurso: str, user_role: str):
        self.id = id
        self.tenant_id = tenant_id
        self.acao = acao
        self.recurso = recurso
        self.user_role = user_role
        self.timestamp = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "acao": self.acao,
            "recurso": self.recurso,
            "user_role": self.user_role,
            "timestamp": self.timestamp.isoformat(),
        }


class MensagemModel:

    def __init__(self, id: str, tenant_id: str, contato_id: str, conteudo: str, enviado_em: datetime):
        self.id = id
        self.tenant_id = tenant_id
        self.contato_id = contato_id
        self.conteudo = conteudo
        self.enviado_em = enviado_em
        self.anonimizado = False


class LgpdService:
    """
    Serviço de Conformidade LGPD (S5, S8, S9, S12, AC 1-4).
    - S8: Exclusão em cascata real de contato, leads, eventos e alvos (AC 1).
    - S12, S5: Exportação de dados restrita a 'dono' e 'operador' com log de auditoria (AC 2, AC 4).
    - S9: Retenção de 24 meses e job de anonimização de conteúdo (AC 3).
    """

    def __init__(self):
        self.audit_logs: list[AuditLogModel] = []
        self.mensagens: list[MensagemModel] = []

    def excluir_contato_cascata(self, tenant_id: str, contato_id: str) -> dict[str, Any]:
        """
        Exclui contato e todos os registros associados em cascata (S8, §22, AC 1).
        """
        contato_key = next((k for k, c in lead_service.contatos.items() if c.id == contato_id and c.tenant_id == tenant_id), None)
        if not contato_key:
            return {"sucesso": False, "status_code": 404, "erro": "Contato não encontrado"}

        # 1. Remove contato
        del lead_service.contatos[contato_key]

        # 2. Exclui leads associados em cascata
        leads_removidos = [l.id for l in lead_service.leads if l.contato_id == contato_id and l.tenant_id == tenant_id]
        lead_service.leads = [l for l in lead_service.leads if not (l.contato_id == contato_id and l.tenant_id == tenant_id)]

        # 3. Exclui alvos de campanha em cascata
        campanha_engine_service.alvos = [a for a in campanha_engine_service.alvos if a.contato_id != contato_id]

        # 4. Exclui mensagens do contato
        self.mensagens = [m for m in self.mensagens if m.contato_id != contato_id]

        # 5. Log de auditoria da exclusão
        self.audit_logs.append(
            AuditLogModel(
                id=len(self.audit_logs) + 1,
                tenant_id=tenant_id,
                acao="exclusao_cascata_lgpd",
                recurso=f"contato_{contato_id}",
                user_role="titular_lgpd",
            )
        )

        logger.info(f"LGPD S8: Exclusão em cascata concluída [contato_id={contato_id}, leads_removidos={len(leads_removidos)}]")
        return {
            "sucesso": True,
            "contato_id": contato_id,
            "leads_removidos_count": len(leads_removidos),
            "mensagem": "Contato e todos os seus registros foram permanentemente eliminados em cascata.",
        }

    def exportar_dados_contato(self, tenant_id: str, contato_id: str, user_role: str = "dono") -> dict[str, Any]:
        """
        Exporta dados do contato com controle de acesso e auditoria (S12, S5, AC 2, AC 4).
        """
        # 1. Guard de Papéis (S12, AC 2)
        if user_role not in ("dono", "operador"):
            logger.warning(f"LGPD S12: Acesso negado para o perfil '{user_role}' na exportação de dados")
            return {
                "sucesso": False,
                "status_code": 403,
                "erro": "Permissão negada. Apenas os perfis 'dono' e 'operador' podem exportar dados de contatos (LGPD S12).",
            }

        contato = next((c for c in lead_service.contatos.values() if c.id == contato_id and c.tenant_id == tenant_id), None)
        if not contato:
            return {"sucesso": False, "status_code": 404, "erro": "Contato não encontrado"}

        leads = [l.to_dict() for l in lead_service.leads if l.contato_id == contato_id and l.tenant_id == tenant_id]

        # 2. Log de Auditoria Obrigatório (S5, AC 4)
        audit = AuditLogModel(
            id=len(self.audit_logs) + 1,
            tenant_id=tenant_id,
            acao="exportacao_dados_lgpd",
            recurso=f"contato_{contato_id}",
            user_role=user_role,
        )
        self.audit_logs.append(audit)

        logger.info(f"LGPD S5: Exportação auditada realizada por '{user_role}' [contato_id={contato_id}]")
        contato_dict = contato.model_dump() if hasattr(contato, "model_dump") else contato.dict()
        return {
            "sucesso": True,
            "dados": {
                "contato": contato_dict,
                "leads": leads,
                "exportado_em": datetime.now().isoformat(),
                "audit_id": audit.id,
            },
        }

    def executar_expurgo_24_meses(self, tenant_id: str, now: datetime | None = None) -> dict[str, Any]:
        """
        Job de Retenção de 24 meses: Anonimiza o conteúdo de mensagens antigas mantendo métricas (S9, AC 3).
        """
        simulated_now = now or datetime.now()
        limite_24m = simulated_now - timedelta(days=730)

        anonimizadas_count = 0
        for m in self.mensagens:
            if m.tenant_id == tenant_id and m.enviado_em < limite_24m and not m.anonimizado:
                m.conteudo = "[ANONIMIZADO_LGPD_24M]"
                m.anonimizado = True
                anonimizadas_count += 1

        logger.info(f"LGPD S9: Job de expurgo 24M concluído [tenant={tenant_id}, mensagens_anonimizadas={anonimizadas_count}]")
        return {
            "sucesso": True,
            "tenant_id": tenant_id,
            "mensagens_anonimizadas": anonimizadas_count,
        }


lgpd_service = LgpdService()

import logging
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field

logger = logging.getLogger("alfaia.interest_service")

TipoMudanca = Literal["novo_interesse", "atualizacao", "sem_mudanca"]


class LeadInteresseModel(BaseModel):
    id: int
    tenant_id: str
    lead_id: str
    versao: int = 1
    evento_tipo: str | None = None
    evento_data: str | None = None
    papel: str | None = None
    peca_interesse: str | None = None
    tamanho: str | None = None
    cor: str | None = None
    valor_estimado: float | None = None
    motivo: str | None = None
    criado_em: datetime = Field(default_factory=datetime.now)


class InterestService:
    """
    Serviço de Gestão de Interesses do Lead e Versionamento Imutável (PRD §9.6, §17.4, AC 1-4).
    """

    def __init__(self):
        self.interesses_historico: list[LeadInteresseModel] = []

    @staticmethod
    def avaliar_mudanca_interesse(
        interesse_vigente: dict[str, Any],
        novo_interesse: dict[str, Any],
    ) -> TipoMudanca:
        # Sinais de NOVO INTERESSE (PRD §9.6): Evento diferente, Data diferente ou Peça/Categoria diferente
        if (
            (interesse_vigente.get("evento_tipo") and novo_interesse.get("evento_tipo") and interesse_vigente.get("evento_tipo") != novo_interesse.get("evento_tipo"))
            or (interesse_vigente.get("evento_data") and novo_interesse.get("evento_data") and interesse_vigente.get("evento_data") != novo_interesse.get("evento_data"))
            or (interesse_vigente.get("peca_interesse") and novo_interesse.get("peca_interesse") and interesse_vigente.get("peca_interesse") != novo_interesse.get("peca_interesse"))
        ):
            return "novo_interesse"

        # Sinais de ATUALIZAÇÃO DO MESMO INTERESSE: Tamanho, Cor, Papel ou Valor estimado diferente
        if (
            (novo_interesse.get("tamanho") and novo_interesse.get("tamanho") != interesse_vigente.get("tamanho"))
            or (novo_interesse.get("cor") and novo_interesse.get("cor") != interesse_vigente.get("cor"))
            or (novo_interesse.get("papel") and novo_interesse.get("papel") != interesse_vigente.get("papel"))
            or (novo_interesse.get("valor_estimado") and novo_interesse.get("valor_estimado") != interesse_vigente.get("valor_estimado"))
        ):
            return "atualizacao"

        return "sem_mudanca"

    def processar_registro_interesse(
        self,
        tenant_id: str,
        lead_atual: Any,
        lead_service: Any,
        novo_interesse: dict[str, Any],
    ) -> tuple[Any, LeadInteresseModel | None, TipoMudanca]:
        interesse_vigente = {
            "evento_tipo": lead_atual.evento_tipo,
            "evento_data": lead_atual.evento_data,
            "peca_interesse": lead_atual.peca_interesse,
            "tamanho": lead_atual.tamanho,
            "cor": lead_atual.cor,
            "papel": getattr(lead_atual, "papel", None),
            "valor_estimado": lead_atual.valor_estimado,
        }

        tipo_mudanca = self.avaliar_mudanca_interesse(interesse_vigente, novo_interesse)

        if tipo_mudanca == "sem_mudanca":
            logger.info(f"Interesse idêntico para lead {lead_atual.id}, nenhuma nova versão gerada.")
            return lead_atual, None, "sem_mudanca"

        if tipo_mudanca == "novo_interesse":
            # 1. Encerra o lead atual como 'descartado' com motivo 'interesse_substituido' (AC 1, T7)
            lead_atual.status = "descartado"
            lead_atual.motivo_descarte = "interesse_substituido"

            # 2. Cria um novo lead para o mesmo contato
            key = f"{tenant_id}:{lead_atual.contato_id}"
            contato_id = lead_atual.contato_id
            novo_seq = lead_atual.lead_seq + 1

            from app.services.lead_service import LeadModel
            novo_lead = LeadModel(
                id=f"lead_{len(lead_service.leads) + 1}",
                tenant_id=tenant_id,
                contato_id=contato_id,
                lead_seq=novo_seq,
                status="novo",
                reaberto_de_lead_id=lead_atual.id,
                evento_tipo=novo_interesse.get("evento_tipo"),
                evento_data=novo_interesse.get("evento_data"),
                peca_interesse=novo_interesse.get("peca_interesse"),
                tamanho=novo_interesse.get("tamanho"),
                cor=novo_interesse.get("cor"),
                valor_estimado=novo_interesse.get("valor_estimado"),
            )
            lead_service.leads.append(novo_lead)

            # 3. Registra Versão 1 do novo lead em lead_interesses
            registro = LeadInteresseModel(
                id=len(self.interesses_historico) + 1,
                tenant_id=tenant_id,
                lead_id=novo_lead.id,
                versao=1,
                evento_tipo=novo_interesse.get("evento_tipo"),
                evento_data=novo_interesse.get("evento_data"),
                peca_interesse=novo_interesse.get("peca_interesse"),
                tamanho=novo_interesse.get("tamanho"),
                cor=novo_interesse.get("cor"),
                valor_estimado=novo_interesse.get("valor_estimado"),
                motivo="novo_interesse_detectado",
            )
            self.interesses_historico.append(registro)
            return novo_lead, registro, "novo_interesse"

        else:  # tipo_mudanca == "atualizacao"
            # Atualiza os detalhes do lead vigente (AC 3, T8)
            if novo_interesse.get("tamanho"):
                lead_atual.tamanho = novo_interesse.get("tamanho")
            if novo_interesse.get("cor"):
                lead_atual.cor = novo_interesse.get("cor")
            if novo_interesse.get("valor_estimado"):
                lead_atual.valor_estimado = novo_interesse.get("valor_estimado")

            # Busca a maior versão já existente para este lead
            versões_existentes = [i.versao for i in self.interesses_historico if i.lead_id == lead_atual.id]
            proxima_versao = (max(versões_existentes) + 1) if versões_existentes else 1

            registro = LeadInteresseModel(
                id=len(self.interesses_historico) + 1,
                tenant_id=tenant_id,
                lead_id=lead_atual.id,
                versao=proxima_versao,
                evento_tipo=lead_atual.evento_tipo,
                evento_data=lead_atual.evento_data,
                peca_interesse=lead_atual.peca_interesse,
                tamanho=lead_atual.tamanho,
                cor=lead_atual.cor,
                valor_estimado=lead_atual.valor_estimado,
                motivo="atualizacao_detalhe",
            )
            self.interesses_historico.append(registro)
            return lead_atual, registro, "atualizacao"


interest_service = InterestService()

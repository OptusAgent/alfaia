import logging
import uuid
from typing import Any
from datetime import datetime

from app.services.contato_segmentacao_service import contato_segmentacao_service

logger = logging.getLogger("alfaia.campanha_service")


class CampanhaModel:

    def __init__(
        self,
        id: str,
        tenant_id: str,
        nome: str,
        segmento: dict[str, Any],
        mensagem_id: str | None = None,
        status: str = "rascunho",
        agendada_para: datetime | None = None,
        total: int = 0,
        enviados: int = 0,
        falhas: int = 0,
        respondidos: int = 0,
    ):
        self.id = id
        self.tenant_id = tenant_id
        self.nome = nome
        self.segmento = segmento
        self.mensagem_id = mensagem_id
        self.status = status
        self.agendada_para = agendada_para
        self.total = total
        self.enviados = enviados
        self.falhas = falhas
        self.respondidos = respondidos
        self.criado_em = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "nome": self.nome,
            "segmento": self.segmento,
            "mensagem_id": self.mensagem_id,
            "status": self.status,
            "agendada_para": self.agendada_para.isoformat() if self.agendada_para else None,
            "total": self.total,
            "enviados": self.enviados,
            "falhas": self.falhas,
            "respondidos": self.respondidos,
            "criado_em": self.criado_em.isoformat(),
        }


class CampanhaService:
    """
    Serviço de Prévia de Segmentação e Rascunho de Campanhas (PRD §15.2, §17.8, AC 1-3).
    - Exclusão estrita de contatos em opt-out tanto da contagem quanto da amostra (AC 3, Regra K3).
    - Cálculo da contagem exata e amostra representativa de até 5 contatos (AC 2).
    - Criação de rascunhos de campanha (Task 4).
    """

    def __init__(self):
        self.campanhas: list[CampanhaModel] = []

    def gerar_previa_campanha(
        self,
        tenant_id: str = "tenant_piloto",
        segmento: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        seg = segmento or {}

        # 1. Consulta contatos com base nos filtros de segmentação
        contatos_filtrados = contato_segmentacao_service.buscar_contatos_segmentados(
            tenant_id=tenant_id,
            tipo_evento=seg.get("tipo_evento"),
            papel=seg.get("papel"),
            status_final_lead=seg.get("status_final_lead"),
            tag=seg.get("tag"),
        )

        # 2. Exclusão estrita de contatos em Opt-Out (AC 3, Regra K3)
        elegiveis = []
        optout_excluidos = 0

        for c in contatos_filtrados:
            if c.get("opt_out") is True:
                optout_excluidos += 1
            else:
                elegiveis.append(c)

        # 3. Extrai amostra representativa de até 5 contatos
        amostra = elegiveis[:5]

        logger.info(f"Prévia de campanha gerada [total_elegiveis={len(elegiveis)}, optout_excluidos={optout_excluidos}]")
        return {
            "sucesso": True,
            "tenant_id": tenant_id,
            "segmento": seg,
            "total_elegiveis": len(elegiveis),
            "optout_excluidos": optout_excluidos,
            "amostra": amostra,
        }

    def criar_campanha_rascunho(
        self,
        tenant_id: str,
        nome: str,
        segmento: dict[str, Any],
        mensagem_id: str | None = None,
        agendada_para: str | None = None,
    ) -> dict[str, Any]:
        previa = self.gerar_previa_campanha(tenant_id=tenant_id, segmento=segmento)
        total_elegiveis = previa["total_elegiveis"]

        campanha_id = str(uuid.uuid4())
        dt_agendada = datetime.fromisoformat(agendada_para) if agendada_para else None

        campanha = CampanhaModel(
            id=campanha_id,
            tenant_id=tenant_id,
            nome=nome,
            segmento=segmento,
            mensagem_id=mensagem_id,
            status="rascunho",
            agendada_para=dt_agendada,
            total=total_elegiveis,
        )
        self.campanhas.append(campanha)

        logger.info(f"Campanha em rascunho criada [id={campanha_id}, nome='{nome}', total={total_elegiveis}]")
        return {"sucesso": True, "campanha": campanha.to_dict()}


campanha_service = CampanhaService()

import logging
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.handoff_service import handoff_service

logger = logging.getLogger("alfaia.conversas_router")
router = APIRouter(prefix="/api/conversas", tags=["Conversas & Transbordo"])

# Armazenamento em memória/mock para endpoints do worker
MEMORIA_CONVERSAS: dict[str, dict[str, Any]] = {
    "c100": {"id": "c100", "tenant_id": "t1", "estado": "ia", "pausada_em": None, "pausada_por": None, "pausada_ate": None}
}


class AssumirConversaRequest(BaseModel):
    atendente_id: str


@router.post("/{conversa_id}/assumir")
async def assumir_conversa_endpoint(conversa_id: str, body: AssumirConversaRequest):
    """
    Endpoint para atendente humano assumir a conversa no Portal (PRD §18.2).
    """
    conversa = MEMORIA_CONVERSAS.get(conversa_id)
    if not conversa:
        # Se não estiver em memória, simula conversa encontrada para teste REST
        conversa = {"id": conversa_id, "estado": "ia"}
        MEMORIA_CONVERSAS[conversa_id] = conversa

    conversa_atualizada = handoff_service.assumir_conversa(conversa, atendente_id=body.atendente_id)
    return {"sucesso": True, "conversa": conversa_atualizada}


@router.post("/{conversa_id}/devolver")
async def devolver_conversa_endpoint(conversa_id: str):
    """
    Endpoint para atendente humano devolver a conversa para a IA no Portal (PRD §18.2).
    """
    conversa = MEMORIA_CONVERSAS.get(conversa_id)
    if not conversa:
        conversa = {"id": conversa_id, "estado": "humano"}
        MEMORIA_CONVERSAS[conversa_id] = conversa

    conversa_atualizada = handoff_service.devolver_para_ia(conversa)
    return {"sucesso": True, "conversa": conversa_atualizada}


@router.get("/leads/{lead_id}/eventos")
async def obter_eventos_timeline_lead(lead_id: str):
    """
    Retorna o histórico cronológico de eventos do lead (PRD §10.4, §17.4, §18.2, AC 1, AC 3).
    """
    from app.services.lead_service import lead_service
    eventos = [e.model_dump() for e in lead_service.eventos if getattr(e, "lead_id", None) == lead_id]
    # Ordena por criado_em decrescente
    eventos.sort(key=lambda x: x.get("criado_em", ""), reverse=True)

    return {
        "sucesso": True,
        "lead_id": lead_id,
        "total_eventos": len(eventos),
        "eventos": eventos,
    }


class DescartarLeadRequest(BaseModel):
    motivo: str
    tenant_id: str = "tenant_piloto"
    autor: str = "humano"


@router.post("/leads/{lead_id}/descartar")
async def descartar_lead_endpoint(lead_id: str, body: DescartarLeadRequest):
    """
    Endpoint para descarte de lead com retenção de dados e histórico (PRD §10.3, §18.2, AC 1, AC 4).
    """
    from app.services.lead_retention_service import lead_retention_service
    res = lead_retention_service.descartar_lead(
        tenant_id=body.tenant_id,
        lead_id=lead_id,
        motivo=body.motivo,
        autor=body.autor,
    )
    if not res.get("sucesso"):
        raise HTTPException(status_code=400, detail=res.get("erro"))
    return res


class DispararFollowupRequest(BaseModel):
    mensagem_id: str
    tenant_id: str = "tenant_piloto"
    canal: str = "uazapi"
    janela_aberta: bool = True
    user_role: str = "atendente"


@router.post("/leads/{lead_id}/followup")
async def disparar_followup_endpoint(lead_id: str, body: DispararFollowupRequest):
    """
    Endpoint para disparo manual de mensagem de follow-up pelo lojista (PRD §18.2, AC 4).
    """
    from app.services.followup_dispatch_service import followup_dispatch_service
    res = followup_dispatch_service.disparar_followup(
        tenant_id=body.tenant_id,
        lead_id=lead_id,
        mensagem_id=body.mensagem_id,
        canal=body.canal,
        janela_aberta=body.janela_aberta,
        user_role=body.user_role,
    )
    if not res.get("sucesso"):
        raise HTTPException(status_code=res.get("status_code", 400), detail=res.get("erro"))
    return res


@router.get("/contatos")
async def obter_base_contatos(
    tenant_id: str = "tenant_piloto",
    tipo_evento: str | None = None,
    papel: str | None = None,
    status_final_lead: str | None = None,
    tag: str | None = None,
):
    """
    Endpoint de consulta da base permanente de contatos com segmentação para remarketing (PRD §15.1, §18.2, AC 1-4).
    """
    from app.services.contato_segmentacao_service import contato_segmentacao_service
    contatos = contato_segmentacao_service.buscar_contatos_segmentados(
        tenant_id=tenant_id,
        tipo_evento=tipo_evento,
        papel=papel,
        status_final_lead=status_final_lead,
        tag=tag,
    )
    return {
        "sucesso": True,
        "tenant_id": tenant_id,
        "total": len(contatos),
        "contatos": contatos,
    }


class PreviaCampanhaRequest(BaseModel):
    tenant_id: str = "tenant_piloto"
    segmento: dict[str, Any] = Field(default_factory=dict)


@router.post("/campanhas/previa")
async def gerar_previa_campanha_endpoint(body: PreviaCampanhaRequest):
    """
    Endpoint para geração de prévia de campanha com contagem exata e amostra sem opt-out (PRD §15.2, §18.2, AC 1-3).
    """
    from app.services.campanha_service import campanha_service
    return campanha_service.gerar_previa_campanha(tenant_id=body.tenant_id, segmento=body.segmento)


class CriarCampanhaRequest(BaseModel):
    nome: str
    tenant_id: str = "tenant_piloto"
    segmento: dict[str, Any] = Field(default_factory=dict)
    mensagem_id: str | None = None
    agendada_para: str | None = None


@router.post("/campanhas")
async def criar_campanha_endpoint(body: CriarCampanhaRequest):
    """
    Endpoint para criação de rascunho de campanha (PRD §17.8, §18.2, Task 4).
    """
    from app.services.campanha_service import campanha_service
    return campanha_service.criar_campanha_rascunho(
        tenant_id=body.tenant_id,
        nome=body.nome,
        segmento=body.segmento,
        mensagem_id=body.mensagem_id,
        agendada_para=body.agendada_para,
    )

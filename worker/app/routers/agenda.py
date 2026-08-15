import logging
from typing import Any
from fastapi import APIRouter, Query
from app.services.agenda_sync_service import agenda_sync_service

logger = logging.getLogger("alfaia.agenda_router")
router = APIRouter(prefix="/api/agenda", tags=["Agenda & Sync WebLocação"])


@router.get("")
async def consultar_agenda_periodo(
    inicio: str = Query("2026-09-01", description="Data início YYYY-MM-DD"),
    fim: str = Query("2026-09-30", description="Data fim YYYY-MM-DD"),
    tipo: str | None = Query(None, description="Filtro por tipo (prova, retirada, ajuste)"),
    origem: str | None = Query(None, description="Filtro por origem (automacao, loja)"),
    tenant_id: str = Query("tenant_piloto", description="ID do tenant"),
):
    """
    Retorna a lista de agendamentos filtrada por intervalo de datas e critérios de origem (PRD §11, §18.2, AC 11.1).
    """
    itens = agenda_sync_service.obter_agendamentos_periodo(
        tenant_id=tenant_id,
        data_inicio=inicio,
        data_fim=fim,
        tipo=tipo,
        origem=origem,
    )
    return {
        "sucesso": True,
        "inicio": inicio,
        "fim": fim,
        "quantidade": len(itens),
        "agendamentos": itens,
    }


@router.post("/sync")
async def disparar_sincronizacao_manual(
    inicio: str = Query("2026-09-01"),
    fim: str = Query("2026-09-30"),
    tenant_id: str = Query("tenant_piloto"),
):
    """
    Dispara sincronização manual sob demanda da agenda com o ERP WebLocação (PRD §11, §18.2, AC 11.3).
    """
    res = agenda_sync_service.sincronizar_agenda_periodo(tenant_id=tenant_id, data_inicio=inicio, data_fim=fim)
    return res

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Any

from app.services.scheduling_service import scheduling_service, AgendamentoModel
from app.services.weblocacao_service import weblocacao_service
from app.services.supabase_rest import supabase_rest_service

logger = logging.getLogger("alfaia.agenda_sync")


class AgendaSyncService:
    """
    Serviço de Sincronização Bidirecional de Agenda e Consulta por Período (PRD §11, §18.3, AC 11.1–11.3).
    - Job de sincronização contínuo portátil a cada 10 min (AC 11.3).
    - Separação de origens 'automacao' vs 'loja' (AC 11.2).
    - Filtragem por período (dia/semana/mês) (AC 11.1).
    """

    def __init__(self):
        self._is_running = False
        self.ultimo_sync_em: datetime | None = None

    def sincronizar_agenda_periodo(
        self,
        tenant_id: str = "tenant_piloto",
        data_inicio: str = "2026-09-01",
        data_fim: str = "2026-09-30",
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Busca agendamentos no ERP WebLocação e faz merge mantendo origens ('loja' vs 'automacao') (AC 2, AC 11.2, AC 11.3).
        """
        simulated_now = now or datetime.now()

        # Busca real no ERP via camada anticorrupção — respeita WL_MODO (mock/real) (story 5.6, AC 3)
        itens_erp = weblocacao_service.listar_agendamentos(
            tenant_id=tenant_id, data_inicio=data_inicio, data_fim=data_fim
        )

        novos_adicionados = 0
        for item in itens_erp:
            # Evita duplicar se já existir na lista local
            ja_existe = any(a.wl_agendamento_id == item.id for a in scheduling_service.agendamentos)
            if not ja_existe:
                novo = AgendamentoModel(
                    id=f"ag_sync_{len(scheduling_service.agendamentos) + 1}",
                    tenant_id=tenant_id,
                    wl_agendamento_id=item.id,
                    lead_id="lead_erp_externo",
                    tipo=item.tipo,
                    data=item.data,
                    hora=item.hora,
                    cliente_nome=item.cliente_nome,
                    cliente_telefone=item.cliente_telefone,
                    produto_ref=item.produto,
                    origem=item.origem,
                    status="ativo",
                    sincronizado_em=simulated_now,
                )
                scheduling_service.agendamentos.append(novo)
                # Persiste em Postgres real (story 5.6, AC 3, AC 5) — 409 tratado como já sincronizado
                # (concorrência entre execuções do loop), não como erro. Falha aqui não interrompe o
                # restante da sincronização (I2).
                try:
                    supabase_rest_service.inserir_agendamento(
                        {
                            "tenant_id": tenant_id,
                            "wl_agendamento_id": item.id,
                            "lead_id": None,
                            "tipo": item.tipo,
                            "data": item.data,
                            "hora": item.hora,
                            "cliente_nome": item.cliente_nome,
                            "cliente_telefone": item.cliente_telefone,
                            "produto_ref": item.produto,
                            "origem": item.origem,
                            "status": "ativo",
                        }
                    )
                except Exception as e:
                    logger.warning(f"Falha inesperada ao persistir agendamento sincronizado (nao bloqueante): {e}")
                novos_adicionados += 1

        self.ultimo_sync_em = simulated_now
        logger.info(f"Sincronização de agenda concluída com sucesso [novos={novos_adicionados}, total={len(scheduling_service.agendamentos)}]")
        return {
            "sucesso": True,
            "novos_sincronizados": novos_adicionados,
            "total_agendamentos": len(scheduling_service.agendamentos),
            "sincronizado_em": simulated_now.isoformat(),
        }

    def obter_agendamentos_periodo(
        self,
        tenant_id: str = "tenant_piloto",
        data_inicio: str = "2026-09-01",
        data_fim: str = "2026-09-30",
        tipo: str | None = None,
        origem: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retorna agendamentos filtrados por intervalo de datas (dia/semana/mês), tipo e origem (AC 1, AC 11.1, AC 11.2).
        Lê do Postgres real quando `supabase_rest_service` está configurado (story 5.6, AC 5); cai para
        a lista em memória do processo como fallback (ambiente sem credencial, ex.: testes).
        """
        if supabase_rest_service.configurado:
            registros_db = supabase_rest_service.listar_agendamentos_periodo(
                tenant_id=tenant_id, data_inicio=data_inicio, data_fim=data_fim, tipo=tipo, origem=origem
            )
            if registros_db is not None:
                return registros_db

        dt_inicio = datetime.fromisoformat(data_inicio).date()
        dt_fim = datetime.fromisoformat(data_fim).date()

        filtrados = []
        for ag in scheduling_service.agendamentos:
            if ag.tenant_id != tenant_id:
                continue

            dt_ag = datetime.fromisoformat(ag.data).date()
            if dt_inicio <= dt_ag <= dt_fim:
                if tipo and ag.tipo.lower() != tipo.lower():
                    continue
                if origem and ag.origem.lower() != origem.lower():
                    continue
                filtrados.append(ag.model_dump())

        # Ordena por data e hora
        filtrados.sort(key=lambda x: (x["data"], x["hora"]))
        return filtrados

    async def loop_worker_agenda_sync(self, intervalo_segundos: float = 600.0):
        """
        Job contínuo portátil de sincronização de agenda a cada 10 min (600s) (AC 3, AC 11.3, PRD §18.3).
        """
        self._is_running = True
        logger.info("Agenda Sync Background Worker iniciado (intervalo 10 min).")
        while self._is_running:
            try:
                self.sincronizar_agenda_periodo()
            except Exception as e:
                logger.error(f"Erro no loop do Agenda Sync Worker: {e}")
            await asyncio.sleep(intervalo_segundos)

    def parar_worker(self):
        self._is_running = False


agenda_sync_service = AgendaSyncService()

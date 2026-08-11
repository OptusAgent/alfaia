import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any
from pydantic import BaseModel, Field

logger = logging.getLogger("alfaia.debounce_service")


class DebounceItemModel(BaseModel):
    id: int
    tenant_id: str
    conversa_id: str
    processar_em: datetime
    bloqueado_em: datetime | None = None
    criado_em: datetime = Field(default_factory=datetime.now)


class DebounceService:
    """
    Serviço de Agrupamento Inbound (Debounce) com consumo por FOR UPDATE SKIP LOCKED (PRD §17.6, AC 1-4).
    Garante que mensagens em rajada do mesmo contato resultem em uma única invocação do motor de IA.
    """

    def __init__(self):
        self.buffer: list[DebounceItemModel] = []
        self._is_running = False

    def agendar_debounce(
        self,
        tenant_id: str,
        conversa_id: str,
        janela_segundos: int = 5,
        now: datetime | None = None,
    ) -> DebounceItemModel:
        simulated_now = now or datetime.now()
        novo_processar_em = simulated_now + timedelta(seconds=janela_segundos)

        # Procura um registro existente não bloqueado para a mesma conversa (Índice único parcial debounce_um_por_conversa)
        item_existente = next(
            (item for item in self.buffer if item.conversa_id == conversa_id and item.bloqueado_em is None),
            None,
        )

        if item_existente:
            # Reagenda a janela de debounce para empurrar o processamento (ex.: +5s a partir da última mensagem)
            item_existente.processar_em = novo_processar_em
            logger.info(f"Debounce reagendado [conversa_id={conversa_id}, novo_processar_em={novo_processar_em}]")
            return item_existente
        else:
            novo_item = DebounceItemModel(
                id=len(self.buffer) + 1,
                tenant_id=tenant_id,
                conversa_id=conversa_id,
                processar_em=novo_processar_em,
                criado_em=simulated_now,
            )
            self.buffer.append(novo_item)
            logger.info(f"Debounce agendado [conversa_id={conversa_id}, processar_em={novo_processar_em}]")
            return novo_item

    def consumir_lote_debounce(
        self,
        limit: int = 20,
        now: datetime | None = None,
    ) -> list[DebounceItemModel]:
        simulated_now = now or datetime.now()

        # Simula a query SQL: SELECT * FROM debounce_buffer WHERE processar_em <= now AND bloqueado_em IS NULL ORDER BY processar_em FOR UPDATE SKIP LOCKED LIMIT 20
        candidatos = [
            item for item in self.buffer
            if item.processar_em <= simulated_now and item.bloqueado_em is None
        ]
        candidatos.sort(key=lambda x: x.processar_em)
        lote = candidatos[:limit]

        # Trava os itens para consumo exclusivo (SKIP LOCKED)
        for item in lote:
            item.bloqueado_em = simulated_now

        if lote:
            logger.info(f"Lote debounce consumido com sucesso [quantidade={len(lote)}]")
        return lote

    async def loop_worker_debounce(self, intervalo_segundos: float = 2.0):
        """Loop contínuo portátil executando dentro do próprio FastAPI worker (sem dependência de Cloud Tasks)."""
        self._is_running = True
        logger.info("Debounce Background Worker iniciado.")
        while self._is_running:
            try:
                lote = self.consumir_lote_debounce()
                for item in lote:
                    # Aqui acionaria o acionamento do motor de IA
                    logger.debug(f"Processando conversa aglutinada [conversa_id={item.conversa_id}]")
            except Exception as e:
                logger.error(f"Erro no loop do debounce worker: {e}")
            await asyncio.sleep(intervalo_segundos)

    def parar_worker(self):
        self._is_running = False


debounce_service = DebounceService()

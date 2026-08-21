import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.routers import webhooks, conversas, agenda
from app.services.followup_worker_service import followup_worker_service

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s",
)

logger = logging.getLogger("alfaia.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Job de plano de fundo portátil (story 6.7, `.claude/rules/alfaia-stack-deploy.md`): roda como
    task asyncio dentro do próprio processo do worker — igual em Cloud Run (dev) e EasyPanel/
    Dockplot (produção), nunca amarrado a Cloud Scheduler/Cloud Tasks.
    """
    tenants = [t.strip() for t in os.getenv("ALFAIA_TENANT_IDS", "tenant_piloto").split(",") if t.strip()]
    task = asyncio.create_task(followup_worker_service.loop_worker_followup(tenants=tenants))
    logger.info(f"Followup Worker iniciado em background [tenants={tenants}]")
    yield
    task.cancel()


app = FastAPI(
    title="ALFAIA Worker Engine",
    description="Motor de mensageria, IA e robôs de atendimento do ALFAIA",
    version="0.1.0",
    lifespan=lifespan,
)

# Inclui rotas de webhook, conversas/transbordo e agenda
app.include_router(webhooks.router)
app.include_router(conversas.router)
app.include_router(agenda.router)


@app.get("/health")
async def health_check():
    """Rota de verificação de integridade pública do worker."""
    return {"status": "ok", "service": "alfaia-worker"}

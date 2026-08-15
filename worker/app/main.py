from fastapi import FastAPI
from app.routers import webhooks, conversas, agenda

app = FastAPI(
    title="ALFAIA Worker Engine",
    description="Motor de mensageria, IA e robôs de atendimento do ALFAIA",
    version="0.1.0",
)

# Inclui rotas de webhook, conversas/transbordo e agenda
app.include_router(webhooks.router)
app.include_router(conversas.router)
app.include_router(agenda.router)


@app.get("/health")
async def health_check():
    """Rota de verificação de integridade pública do worker."""
    return {"status": "ok", "service": "alfaia-worker"}

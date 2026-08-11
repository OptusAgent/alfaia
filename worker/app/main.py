from fastapi import FastAPI
from app.routers import webhooks

app = FastAPI(
    title="ALFAIA Worker Engine",
    description="Motor de mensageria, IA e robôs de atendimento do ALFAIA",
    version="0.1.0",
)

# Inclui rotas de webhook
app.include_router(webhooks.router)


@app.get("/health")
async def health_check():
    """Rota de verificação de integridade pública do worker."""
    return {"status": "ok", "service": "alfaia-worker"}

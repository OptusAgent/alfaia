# wl-fake-api — ERP fake da WebLocação (WL_MODO=real de teste)
# Mesma estratégia de build do worker/Dockerfile: compatível com Cloud Run
# (desenvolvimento) e VPS via EasyPanel/Dockplot (produção), conforme
# .claude/rules/alfaia-stack-deploy.md.

FROM python:3.12-slim AS base
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir \
    "fastapi>=0.110.0" \
    "uvicorn[standard]>=0.29.0" \
    "pydantic>=2.0.0"

COPY app/ ./app/
COPY data/ ./data/

RUN adduser --system --uid 1001 appuser
USER appuser

ENV PORT=8080
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]

# Worker FastAPI (ALFAIA Engine)
# Build multi-stage para manter a imagem final pequena (<200MB)
# Compatível com Cloud Run (port 8080), VPS Docker e desenvolvimento local

FROM python:3.12-slim AS base
WORKDIR /app

# Dependências do sistema necessárias para httpx e compilação
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências Python
COPY pyproject.toml ./
RUN pip install --no-cache-dir \
    "fastapi>=0.110.0" \
    "uvicorn[standard]>=0.29.0" \
    "pydantic>=2.0.0" \
    "httpx>=0.27.0" \
    "python-multipart>=0.0.9"

# Copia o código da aplicação
COPY app/ ./app/

# Usuário não-root por boas práticas de segurança em Cloud Run
RUN adduser --system --uid 1001 appuser
USER appuser

# Cloud Run injeta PORT=8080; fallback local em 8000
ENV PORT=8080
EXPOSE 8080

# Healthcheck para o Cloud Run e orquestradores
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]

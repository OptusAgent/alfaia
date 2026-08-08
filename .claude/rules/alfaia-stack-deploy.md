# ALFAIA — Stack e Estratégia de Deploy (regra de projeto)

> Esta regra é específica do produto ALFAIA (não do framework AIOX genérico). Complementa `PRD-ALFAIA-v2.md` §6, §18 e §24, e é espelhada em detalhe em `docs/framework/tech-stack.md`.

## Stack

- **Portal:** Next.js 15 (App Router)
- **Worker:** FastAPI (Python)
- **Banco:** Supabase (Postgres + Auth + Realtime + Storage) — único banco em toda fase do produto, não migra entre ambientes
- **IA:** Anthropic API + OpenAI API (transcrição)
- **Canal:** UAZAPI (não oficial) e Meta Cloud API via AuctaFlux/BSP (oficial), atrás de um adapter único

`frontend/` (Vite + React 19, dados mock, Gemini client-side) é protótipo de UX/apresentação — congelado, não é o Portal de produção. Ver `docs/framework/tech-stack.md` §2 antes de reaproveitar qualquer componente dele.

## Estratégia de ambientes (definida em 08/08/2026)

| Fase | Infra | Motivo |
|---|---|---|
| Desenvolvimento e testes | **Cloud Run (GCP)** | Iteração rápida, escala a zero, zero gestão de servidor durante o build do produto |
| Produção — pós-venda / apresentação ao cliente | **VPS: EasyPanel (Hostinger) ou Dockplot (Contabo)** | Custo fixo previsível e controle total do host depois que o cliente fecha |
| Banco de dados | **Supabase**, em todas as fases | Não faz parte da migração de infra — é constante |

**Consequência de projeto (aplicar a toda story que toque infraestrutura, jobs agendados ou deploy):**

1. Portal e Worker precisam de `Dockerfile` — é o denominador comum entre Cloud Run e EasyPanel/Dockplot.
2. Jobs agendados (§18.3 do PRD: `debounce_worker`, `followup_scan`, `agenda_sync`, etc.) são implementados de forma portável (loop/cron dentro do próprio worker) — nunca amarrados a Cloud Scheduler/Cloud Tasks ou qualquer serviço proprietário do GCP sem equivalente rodável em VPS.
3. Nenhum código assume qual dos dois provedores de VPS (EasyPanel/Hostinger ou Dockplot/Contabo) será usado na fase de produção — essa escolha é comercial, decidida após a venda, não técnica.
4. Variáveis de ambiente seguem o padrão do PRD §24 (`SUPABASE_URL`, `WORKER_URL`, `WEBHOOK_INTERNAL_TOKEN`, etc.) — sem hardcode específico de provedor de nuvem.

## Pendência formal

Esta estratégia de deploy (Cloud Run → VPS) ainda **não está registrada no PRD §24**, que hoje só define `local` e `producao` sem detalhar o provedor. Antes de qualquer story de E9 (Operação, S-34/S-35) entrar em desenvolvimento, **@po deve emendar o PRD** para incorporar formalmente esta seção — conforme a nota de método do próprio PRD ("nenhuma decisão de produto ou de arquitetura pode ser tomada dentro de uma story sem estar aqui").

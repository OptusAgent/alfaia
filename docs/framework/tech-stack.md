# ALFAIA — Tech Stack

> Fonte normativa: `PRD-ALFAIA-v2.md` §6, §18, §24. Qualquer stack não listada aqui exige emenda do @po ao PRD antes de uso em story.

## 1. Stack de produção (alvo)

| Camada | Tecnologia | Papel |
|---|---|---|
| **Portal** | Next.js 15 (App Router, route handlers) | Interface web: Kanban, agenda, contatos, campanhas, config |
| **Worker** | FastAPI (Python) | Webhooks de canal, motor de IA, debounce, jobs agendados |
| **Banco de dados** | Supabase (Postgres + Auth + Realtime + Storage) | Persistência multi-tenant, RLS, sessões realtime do portal |
| **LLM / IA** | Anthropic API + OpenAI API (transcrição) | Motor conversacional com tool calling; transcrição de áudio |
| **Canal WhatsApp** | UAZAPI (não oficial) + Meta Cloud API via AuctaFlux/BSP (oficial) | Adapters intercambiáveis atrás de uma interface única (P6, A2, A3) |
| **ERP externo** | WebLocação (REST) | Produtos (leitura) e agenda (leitura/escrita) — nunca fonte de verdade interna |

Este é o único stack válido para código de produção (`/portal`, `/worker`). Nenhuma story pode introduzir uma tecnologia fora desta tabela sem passar antes pelo Spec Pipeline (`.claude/rules/workflow-execution.md`) e emenda do PRD.

## 2. Protótipo de frontend existente — status e limites

`frontend/` é um protótipo visual gerado no Google AI Studio (Vite + React 19 + `@google/genai`, dados 100% mock em `src/frontend/data/mockData.ts`). **Não é o Portal de produção.**

| Aspecto | Protótipo (`frontend/`) | Portal de produção (alvo) |
|---|---|---|
| Framework | Vite + React 19 (SPA) | Next.js 15 (App Router) |
| Dados | Mock local (`mockData.ts`) | Supabase (Postgres real, RLS, realtime) |
| IA | Chamada client-side ao Gemini (`@google/genai`) | Worker FastAPI server-side, Anthropic/OpenAI, nunca no client |
| Autenticação | Nenhuma | Supabase Auth + RBAC (§4.2) |
| Multi-tenant | Nenhum | `tenant_id` em toda tabela, RLS (A1) |
| Uso pretendido | Validação de UX/IA visual e apresentação a stakeholders | — |

**Regra de uso:** o protótipo é referência de design e de comportamento de UI (ver `frontend/src/frontend/ANALYSIS.md` para o mapeamento componente-a-componente). Nenhum componente dele é portado 1:1 para o Portal sem revalidação de dados reais, RLS e permissões. Ele não deve ganhar novas features de negócio — é congelado como referência visual.

## 3. Ambientes e deploy

O PRD (§24) define apenas `local` e `producao`, sem staging. **Esta seção estende §24 com a estratégia de infraestrutura definida em 08/08/2026** (pendente de emenda formal do @po no PRD):

| Fase | Ambiente | Onde roda | Uso |
|---|---|---|---|
| Desenvolvimento e testes | Cloud Run (GCP) | Portal + Worker | Iteração rápida, ambiente descartável/escalável a zero, sem gestão de servidor |
| Pós-venda / produção do cliente | VPS — EasyPanel (Hostinger) **ou** Dockplot (Contabo) | Portal + Worker | Após fechamento comercial e apresentação ao cliente; custo fixo previsível, controle total do host |
| Banco de dados (todas as fases) | Supabase | Postgres + Auth + Realtime + Storage | Único banco em todas as fases — não migra com o resto da infra |
| **wl-fake-api** (dev/teste apenas) | Cloud Run (GCP) ou local | Não faz parte da stack de produção do cliente | ERP fake da WebLocação, para exercitar `WL_MODO=real` sem depender do contrato real ainda não fechado (§7, Q1–Q3). Segue o mesmo requisito de `Dockerfile` portável, mas nunca é implantado na VPS do cliente — ver `wl-fake-api/README.md` |

**Implicações de arquitetura:**
- Portal e Worker DEVEM ser containerizáveis via Docker (`Dockerfile` em cada serviço) desde o início — é o requisito comum a Cloud Run e a EasyPanel/Dockplot.
- Nenhuma dependência de serviço exclusivo do Cloud Run (ex.: Cloud Tasks, Cloud Scheduler nativo) sem um fallback equivalente rodável em VPS — os jobs agendados de §18.3 devem ser implementados de forma portável (loop/cron interno ao worker, não integração proprietária GCP).
- Variáveis de ambiente e secrets seguem o padrão de §24 (`SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, etc.) em ambos os hosts — sem hardcode específico de provedor.
- A escolha entre EasyPanel/Hostinger e Dockplot/Contabo para a fase de produção é decisão comercial pós-venda, não técnica; o código não deve assumir qual dos dois será usado.
- Esta decisão de infraestrutura ainda não está formalizada no PRD §24 — @po deve emendar antes da story de deploy (S-34/E9) entrar em desenvolvimento.

## 4. Variáveis de ambiente (produção)

```
SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_ANON_KEY
WORKER_URL, WEBHOOK_INTERNAL_TOKEN, APP_URL
ANTHROPIC_API_KEY, OPENAI_API_KEY
WL_MODO=mock|real
UAZAPI_BASE_URL
AUCTAFLUX_BASE_URL, AUCTAFLUX_RESELLER_API_KEY
META_WEBHOOK_HMAC_ENFORCE=true|false
```

Ver `PRD-ALFAIA-v2.md` §24 para a lista normativa. `.env.example` na raiz cobre variáveis de tooling AIOX (não confundir com as variáveis de runtime do produto acima).

## 5. Fora de escopo de stack (v1)

App mobile nativo, BI avançado, canais além de WhatsApp (Instagram DM, e-mail, site) — PRD §5.2.

# ALFAIA — Source Tree

## 1. Árvore atual (08/08/2026)

```
ALFAIA/
├── PRD-ALFAIA-v2.md          # Fonte única de verdade do produto (SSOT) — v2.0
├── alfaia-v2.html            # Protótipo estático original (pré-React), referência histórica
├── frontend/                 # Protótipo visual (Vite + React 19), NÃO é o Portal de produção
│   └── src/frontend/         # Componentes mapeados no PRD/UX (ver ANALYSIS.md local)
├── docs/
│   └── framework/            # Este diretório — regras sempre carregadas pelo @dev (devLoadAlwaysFiles)
├── .aiox-core/                # Framework AIOX (L1/L2 — não modificar, ver CLAUDE.md)
└── .claude/                  # Configuração Claude Code: agents, rules, skills, commands
```

**Não existem ainda:** `/portal` (Next.js), `/worker` (FastAPI), `/supabase` (migrations), `docs/prd/` (PRD sharded), `docs/architecture/`, `docs/stories/`, `docs/qa/`. O `core-config.yaml` do AIOX já referencia esses caminhos (`prdShardedLocation: docs/prd`, `devStoryLocation: docs/stories`, `architectureShardedLocation: docs/architecture`) — são criados pelos workflows normais (`@sm *draft`, Spec Pipeline) conforme o desenvolvimento avança, não devem ser criados vazios antecipadamente.

## 2. Árvore alvo (produção — projeção a partir do PRD §6, §18, §24)

```
ALFAIA/
├── PRD-ALFAIA-v2.md
├── docs/
│   ├── framework/             # tech-stack.md, coding-standards.md, source-tree.md (este arquivo)
│   ├── prd/                   # PRD sharded por seção (gerado pelo @po/@sm)
│   ├── architecture/          # Documento de arquitetura sharded (gerado pelo @architect)
│   ├── stories/                # Stories S-01..S-36 (E1..E9, ver PRD §25.2)
│   └── qa/                    # Gates de QA por story
├── portal/                    # Next.js 15 — App Router
│   ├── app/api/                # Route handlers de §18.2 (leads, conversas, agenda, produtos, contatos, campanhas, canais, automacoes)
│   ├── app/(dashboard)/        # Kanban, agenda, contatos, campanhas, config — telas do portal
│   └── lib/                    # RBAC guard (has_permission), client Supabase (anon key)
├── worker/                    # FastAPI
│   ├── adapters/                # Interface única de canal (A2) — uazapi.py, meta.py
│   ├── identificacao/           # identificar_lead, contexto, retomada/reengajamento (E3)
│   ├── motor_ia/                # Tool calling, prompt de sistema (§19), regras invioláveis
│   ├── integracao_wl/           # Camada anticorrupção WebLocação (I7) — mock e real (WL_MODO)
│   ├── crm/                     # Engine de follow-up, descarte, timeline
│   ├── campanhas/                # Engine de campanha (K1–K8)
│   ├── jobs/                     # debounce_worker, followup_scan, agenda_sync, etc. (§18.3) — portáveis, sem dependência de scheduler de nuvem
│   └── webhooks/                  # /webhook/uazapi/{token}, /webhook/meta/{canal_id}
├── supabase/
│   └── migrations/               # Schema, enums, RLS (S-01)
├── frontend/                   # Protótipo congelado — referência de UX, não recebe features novas
└── .aiox-core/, .claude/       # Framework AIOX (inalterado)
```

## 3. Regras de organização

- `/portal` e `/worker` são serviços independentes, cada um com seu próprio `Dockerfile` (requisito para Cloud Run e VPS — ver `tech-stack.md` §3). Não compartilham processo em runtime.
- `frontend/` permanece como está, sem virar dependência de build de `/portal`. É consultado como referência (`frontend/src/frontend/ANALYSIS.md` mapeia componente → função), não importado.
- Migrations em `supabase/migrations/` são a única forma de alterar schema — nunca alteração manual via dashboard do Supabase sem migration correspondente versionada.
- Cada módulo do worker (`adapters/`, `identificacao/`, `motor_ia/`, etc.) corresponde a um épico do PRD §25.2 (E2, E3, E4...) — ao criar uma story nova, o código dela pertence ao módulo do épico, não a um novo diretório ad-hoc.
- Imports absolutos a partir da raiz de cada serviço (Artigo VI da Constitution) — configurar `paths` no `tsconfig.json` do portal e pacote instalável (ou `pyproject.toml` com `src/` layout) no worker.

## 4. Camadas de proteção AIOX (contexto do CLAUDE.md raiz)

| Camada | Paths | Mutabilidade |
|---|---|---|
| L1 Framework Core | `.aiox-core/core/`, `.aiox-core/constitution.md` | Nunca modificar |
| L2 Framework Templates | `.aiox-core/development/*` | Extend-only |
| L3 Project Config | `.aiox-core/data/`, `core-config.yaml` | Mutável com exceções |
| L4 Project Runtime | `docs/stories/`, `portal/`, `worker/`, `supabase/`, `tests/` | Sempre mutável — é aqui que o trabalho do produto acontece |

# EPIC-8: Configuração

**Status:** Planning
**Fase PRD:** *sem fase F dedicada em §25.1 — mapeamento proposto pelo @pm, a validar: adjacente a F7 (Piloto), pois onboarding de tenant e ajuste de prompt precedem a operação com cliente real.*
**Fonte:** `PRD-ALFAIA-v2.md` §16 (M9 — Automações), §19 (Prompt de sistema), §17.2 (Tenancy), §4 (Personas)

---

## Objetivo

Implementar automações e toggles configuráveis por tenant, os parâmetros de prompt/persona/parâmetros da IA, e o fluxo de onboarding de um novo tenant.

## Escopo

**IN:**
- Automações e toggles (§16)
- Prompt, persona e parâmetros (§19.1–19.2)
- Onboarding de tenant (§17.2 Tenancy, §4 Personas)

**OUT:** observabilidade e LGPD (E9).

## Stories

| ID | Story | Complexidade | ACs rastreados (§26) |
|---|---|---|---|
| S-32 | Automações e toggles | S | §16, §19 |
| S-33 | Prompt, persona e parâmetros | M | §16, §19 |
| S-34 | Onboarding de tenant | M | *sem mapeamento em §26 — ver Observações* |

## Dependências

- **Depende de:** E1 (Fundação — tenancy), E4 (Atendimento — prompt/persona consumidos pelo motor de IA, §19).

## Critérios de sucesso

- Critérios de aceite de §19.3 atendidos para S-32/S-33.

## Observações

- S-34 não possui AC na matriz de rastreabilidade §26. @po deve fundamentar a story referenciando §17.2 (Tenancy) e §4 (Personas e RBAC) antes de aprovar, conforme item 1 do DoR (§27.1).
- A regra de projeto [alfaia-stack-deploy.md](../../.claude/rules/alfaia-stack-deploy.md) cita "E9 (Operação, S-34/S-35)" ao descrever a pendência de deploy — mas o PRD §25.2 coloca **S-34 neste épico (E8)**, não em E9. Discrepância a resolver pelo @po junto com a emenda do PRD §24 (ver EPIC-9).

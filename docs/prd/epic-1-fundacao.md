# EPIC-1: Fundação

**Status:** Planning
**Fase PRD:** F0 — Fundação (PRD §25.1, Semana 1)
**Fonte:** `PRD-ALFAIA-v2.md` §4.2, §6, §17, §17.11, §22

---

## Objetivo

Estabelecer a base técnica sobre a qual todos os demais épicos dependem: schema multi-tenant, RLS, autenticação/RBAC e o shell de navegação do Portal. Nenhum outro épico pode iniciar antes deste.

## Escopo

**IN** (rastreado ao PRD):
- Schema base, enums e Row Level Security (§17, §17.11)
- Autenticação, tenancy e RBAC (§4.2 Papéis e permissões)
- Shell do Portal (Next.js) e navegação (§6.1 Componentes)

**OUT:** qualquer funcionalidade de negócio (canal, IA, CRM) — cobertas pelos épicos seguintes.

## Stories

| ID | Story | Complexidade | ACs rastreados (§26) |
|---|---|---|---|
| S-01 | Schema base, enums e RLS | M | RBAC §4.2, RLS §17.11, S1 |
| S-02 | Auth, tenancy e RBAC | M | RBAC §4.2, RLS §17.11, S1 |
| S-03 | Shell do portal e navegação | S | *sem mapeamento em §26 — ver Observações* |

## Dependências

- **Depende de:** nenhuma (épico fundacional).
- **Bloqueia:** todos os demais épicos (E2–E9).

## Critérios de sucesso

- RLS validada por tenant conforme §17.11.
- RBAC aplicado conforme matriz de papéis §4.2.
- Definition of Ready/Done do PRD (§27) aplicável a cada story.

## Observações

- S-03 não possui AC formalmente listado na matriz de rastreabilidade §26. Ao validar esta story, @po deve referenciar explicitamente §6.1 (Componentes) como fundamentação, conforme exige o item 1 do DoR (§27.1).

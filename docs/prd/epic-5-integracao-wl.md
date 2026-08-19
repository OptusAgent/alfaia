# EPIC-5: Integração WebLocação

**Status:** Planning
**Fase PRD:** F4 — Integração WL (PRD §25.1, Semana 7)
**Fonte:** `PRD-ALFAIA-v2.md` §7 (Integração WebLocação), §11 (M4 — Agenda), §12 (M5 — Consulta de produtos)

---

## Objetivo

Construir a camada anticorrupção contra o ERP WebLocação (mock → real), consulta de produtos, slots e criação de agendamento, e sincronização de agenda.

## Escopo

**IN:**
- Camada anticorrupção e mock (§7.2 Contrato esperado, §7.3 Regras de integração)
- Consulta de produtos (§12)
- Slots e criação de agendamento (§11)
- Sync de agenda e tela por período (§11)

**OUT:** motor de IA (E4) — este épico expõe as tools que o motor consome, não o motor em si.

## Stories

| ID | Story | Complexidade | ACs rastreados (§26) |
|---|---|---|---|
| S-19 | Camada anticorrupção e mock | M | AC 12.1–12.4, I1–I8 |
| S-20 | Consulta de produtos | M | AC 12.1–12.4, I1–I8 |
| S-21 | Slots e criação de agendamento | M | AC 12.1–12.4, I1–I8 |
| S-22 | Sync de agenda e tela por período | M | AC 11.1–11.4 |
| — (5.6) | Persistência real de wl_chamadas e agendamentos | M | I3, I6, AC 11.2–11.3 |

Story 5.6 é emergente, criada em 2026-08-19 a partir de um achado de @devops durante ativação em produção (S-19/S-21/S-22 fechadas como `Done` sem que `wl_chamadas`/`agendamentos` de fato persistissem no Postgres — ver `docs/stories/5.6.story.md`). Sem ID `S-` original do PRD.

## Dependências

- **Depende de:** E1 (Fundação).
- **Pode rodar em paralelo** a E3/E4 usando `WL_MODO=mock` (§24) enquanto o contrato real não fecha.

## Critérios de sucesso

- Critérios de §7.3 (Regras de integração) e §11.4 atendidos.

## Observações / Gate

Três questões abertas do PRD (§29) bloqueiam a implementação real (não o mock):

| # | Questão | Bloqueia |
|---|---|---|
| Q1 | Contrato exato dos endpoints da WebLocação | S-20, S-21 |
| Q2 | Slots por vaga ou horário fixo? Capacidade simultânea? | S-21 |
| Q3 | Agendamento exige cliente já cadastrado no ERP, ou aceita nome + telefone? | S-21 |

Responsável por todas: WebLocação (externo ao squad).

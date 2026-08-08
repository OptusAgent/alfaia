# EPIC-3: Identificação

**Status:** Planning
**Fase PRD:** F2 — Identificação (PRD §25.1, Semana 4)
**Fonte:** `PRD-ALFAIA-v2.md` §9 (M2 — Identificação, retomada e reengajamento do lead)

---

## Objetivo

Implementar a função `identificar_lead`, a montagem de contexto do lead, a retomada/reengajamento de conversa e a movimentação automática de status. Este épico é **pré-requisito funcional explícito** do motor de atendimento (E4): "F2 precede F3: o motor de IA depende do contexto de identificação para funcionar corretamente" (PRD §25.1).

## Escopo

**IN:**
- Função `identificar_lead` e migration (§9.3)
- Montagem do contexto do lead entregue à IA (§9.5)
- Retomada e reengajamento na conversa (§9.6)
- Histórico de interesse e detecção de mudança (§9.6)
- Movimentação automática de status — regras MV1–MV6 (§9.7)

**OUT:** motor de IA em si (E4), integração com WebLocação (E5).

## Stories

| ID | Story | Complexidade | ACs rastreados (§26) |
|---|---|---|---|
| S-09 | Função `identificar_lead` e migration | M | AC 9.1, 9.2, 9.5, T1, T2, T5, T6, T9 |
| S-10 | Montagem do contexto do lead | M | AC 9.3, 9.4 |
| S-11 | Retomada e reengajamento na conversa | M | AC 9.4, AC 19.3, T3, T4 |
| S-12 | Histórico de interesse e detecção de mudança | M | AC 9.6, 9.7, T7, T8 |
| S-13 | Movimentação automática de status e regras MV1–MV6 | L | AC 9.8–9.12, T10, T11 |

## Dependências

- **Depende de:** E1 (Fundação), E2 (Canal).
- **Bloqueia:** E4 (Atendimento) — dependência explícita do PRD, não inferida.

## Critérios de sucesso

- Todos os critérios de §9.10 atendidos.
- Casos de teste obrigatórios de §23.2 (derivados de §9) passando.

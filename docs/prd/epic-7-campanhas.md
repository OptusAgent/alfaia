# EPIC-7: Campanhas

**Status:** Planning
**Fase PRD:** F6 — Base e campanhas (PRD §25.1, Semana 10)
**Fonte:** `PRD-ALFAIA-v2.md` §15 (M8 — Base de contatos e campanhas), §9.13/§9.14 (inferência de origem)

---

## Objetivo

Implementar a base de contatos com tags, segmentação com prévia, motor de campanha (regras K1–K8) e opt-out/reversão.

## Escopo

**IN:**
- Base de contatos e tags (§15.1)
- Segmentação e prévia (§15.2)
- Motor de campanha com regras K1–K8 (§15.2)
- Opt-out e reversão (§15.2)

**OUT:** CRM Kanban (E6, já implementado antes na sequência de fases).

## Stories

| ID | Story | Complexidade | ACs rastreados (§26) |
|---|---|---|---|
| S-28 | Base de contatos e tags | M | AC 15.1–15.7, AC 9.13, 9.14, T12 |
| S-29 | Segmentação e prévia | M | AC 15.1–15.7, AC 9.13, 9.14, T12 |
| S-30 | Motor de campanha com K1–K8 | L | AC 15.1–15.7, AC 9.13, 9.14, T12 |
| S-31 | Opt-out e reversão | S | AC 15.1–15.7, AC 9.13, 9.14, T12 |

## Dependências

- **Depende de:** E2 (Canal — envio em massa), E3 (Identificação — histórico de interesse usado na segmentação).

## Critérios de sucesso

- Critérios de aceite de §15.3 atendidos.

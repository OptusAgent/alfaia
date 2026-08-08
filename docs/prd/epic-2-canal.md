# EPIC-2: Canal

**Status:** Planning
**Fase PRD:** F1 — Canal (PRD §25.1, Semanas 2–3)
**Fonte:** `PRD-ALFAIA-v2.md` §14 (M7 — Canal WhatsApp dual)

---

## Objetivo

Implementar o adapter único de canal que abstrai UAZAPI (não oficial) e Meta Cloud API via AuctaFlux/BSP (oficial), com seletor dinâmico, idempotência de webhook e bloqueio pela janela de 24h do WhatsApp.

## Escopo

**IN:**
- Interface do adapter e capabilities (§14.2)
- Adapter UAZAPI — envio + webhook (§14.1)
- Adapter Meta/AuctaFlux — envio + webhook + validação HMAC (§14.1, §14.4)
- Idempotência e captura de webhook (§14.4)
- Seletor de canal e bloqueio por janela de 24h (§14.3)

**OUT:** lógica de identificação de lead ou motor de IA — cobertos por E3 e E4.

## Stories

| ID | Story | Complexidade | ACs rastreados (§26) |
|---|---|---|---|
| S-04 | Interface do adapter e capabilities | S | AC 14.1–14.7 |
| S-05 | Adapter UAZAPI (envio + webhook) | M | AC 14.1–14.7 |
| S-06 | Adapter Meta/AuctaFlux (envio + webhook + HMAC) | L | AC 14.1–14.7 |
| S-07 | Idempotência e captura de webhook | S | AC 14.1–14.7 |
| S-08 | Seletor de canal e bloqueio por janela de 24h | M | AC 14.1–14.7 |

## Dependências

- **Depende de:** E1 (Fundação) — tenancy e auth para escopar webhooks por tenant.
- **Bloqueia:** E3, E4 e E7 (dependem de canal ativo).

## Critérios de sucesso

- Todos os critérios de aceite de §14.5 atendidos.
- Segurança do canal validada conforme §14.4 (HMAC, idempotência).

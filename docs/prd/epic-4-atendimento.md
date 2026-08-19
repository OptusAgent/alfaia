# EPIC-4: Atendimento

**Status:** Planning
**Fase PRD:** F3 — Atendimento (PRD §25.1, Semanas 5–6)
**Fonte:** `PRD-ALFAIA-v2.md` §8 (M1 — Atendimento IA), §13 (M6 — Transbordo)

---

## Objetivo

Implementar o motor de IA com registro de tools, debounce de mensagens, transcrição de áudio, painel de conversa realtime e o fluxo de transbordo (assumir/devolver) para atendimento humano.

## Escopo

**IN:**
- Debounce com `SKIP LOCKED` (§8.3 Pipeline de processamento)
- Motor de IA e registro de tools (§8.2 Ferramentas do motor)
- Transcrição de áudio (§8.3)
- Painel de conversa realtime (§17.12 Realtime)
- Transbordo: assumir e devolver (§13.1, §13.2)

**OUT:** integração com WebLocação real (E5 — usa mock até então).

## Stories

| ID | Story | Complexidade | ACs rastreados (§26) |
|---|---|---|---|
| S-14 | Debounce com SKIP LOCKED | M | AC 8.4 |
| S-15 | Motor de IA e registro de tools | L | AC 8.1, 8.2, 8.3, 8.7, AC 19.1, 19.2 |
| S-16 | Transcrição de áudio | S | AC 8.5 |
| S-17 | Painel de conversa realtime | M | AC 8.6, NFR9 (§20) |
| S-18 | Transbordo: assumir e devolver | M | AC 13.1–13.5 |
| — (4.8) | Conectar tool-calling real da IA (OpenRouter function calling) | L | AC 8.2, 8.3, I5, P3 |

Story 4.8 é emergente, criada em 2026-08-19 a partir de um achado de @devops durante a ativação da story 5.6: mesmo com S-15 (4.3) `Done`, a IA nunca chama tool nenhuma quando o LLM responde de verdade — só no fallback por keyword-match usado em desenvolvimento sem `OPENROUTER_API_KEY`. Ver `docs/stories/4.8.story.md`. Sem ID `S-` original do PRD.

## Dependências

- **Depende de:** E3 (Identificação) — bloqueante, dependência explícita do PRD (§25.1).
- **Bloqueia:** E6 (CRM, parcialmente — timeline/kanban consomem estado de conversa).

## Critérios de sucesso

- Critérios de aceite de §8.4 (M1) e §13 (Transbordo, via matriz §26: AC 13.1–13.5) atendidos.

## Observações / Gate

- **Questão aberta Q8** (§29): "Qual modelo de LLM equilibra custo e qualidade dentro do NFR11?" — responsável Optus Agent, bloqueia S-15. Deve ser resolvida antes de S-15 entrar em desenvolvimento (viola item 3 do DoR §27.1 — "nenhuma decisão de produto pendente dentro da story" — enquanto aberta).

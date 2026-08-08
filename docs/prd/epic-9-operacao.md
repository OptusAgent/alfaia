# EPIC-9: Operação

**Status:** Planning — desbloqueado (ver Gate abaixo, resolvido em 08/08/2026)
**Fase PRD:** *sem fase F dedicada em §25.1 — mapeamento proposto pelo @pm, a validar: alinhado a F7 (Piloto), pois observabilidade e conformidade LGPD são pré-requisito de operar com cliente real.*
**Fonte:** `PRD-ALFAIA-v2.md` §21 (Observabilidade e tratamento de erros), §22 (Segurança e LGPD), §24 (Ambientes e deploy)

---

## Objetivo

Garantir observabilidade (logs estruturados, matriz de erros, alertas) e conformidade LGPD (exportação e exclusão de dados) antes da operação com cliente real.

## Escopo

**IN:**
- Observabilidade e alertas (§21.1–21.3)
- Exportação e exclusão LGPD (§22)

**OUT:** infraestrutura de deploy em si (tratada como pré-requisito/gate, não como story deste épico).

## Stories

| ID | Story | Complexidade | ACs rastreados (§26) |
|---|---|---|---|
| S-35 | Observabilidade e alertas | M | §21 |
| S-36 | Exportação e exclusão LGPD | S | S8, S12 (§22) |

## Dependências

- **Depende de:** todos os épicos anteriores (observa e protege o sistema completo).

## Critérios de sucesso

- Alertas de §21.3 configurados e testados.
- Fluxos de exportação/exclusão de §22 validados.

## Gate — RESOLVIDO em 08/08/2026

O PRD §24 foi emendado pelo @po (v2.0 → v2.1, ver `PRD-ALFAIA-v2.md` §24.1–§24.4) incorporando formalmente a estratégia de deploy Cloud Run (dev/teste) → VPS EasyPanel/Dockplot (produção pós-venda), com Supabase constante. S-35 e S-36 (stories 9.1 e 9.2) estão liberadas — Status atualizado para `Ready`.

Nota de discrepância: a regra de projeto referencia "S-34/S-35" para E9, mas §25.2 do PRD coloca S-34 em E8. Ver observação equivalente em `epic-8-configuracao.md`.

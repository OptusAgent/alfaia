# Épicos ALFAIA — Índice

Materializados a partir de `PRD-ALFAIA-v2.md` §25 (Roadmap, épicos e stories) e §26 (Matriz de rastreabilidade). Nenhum épico ou story foi inventado — toda linha aqui tem seção-fonte no PRD.

## Épicos

| Épico | Arquivo | Fase PRD (§25.1) | Stories |
|---|---|---|---|
| E1 Fundação | [epic-1-fundacao.md](epic-1-fundacao.md) | F0 | S-01 a S-03 |
| E2 Canal | [epic-2-canal.md](epic-2-canal.md) | F1 | S-04 a S-08 |
| E3 Identificação | [epic-3-identificacao.md](epic-3-identificacao.md) | F2 | S-09 a S-13 |
| E4 Atendimento | [epic-4-atendimento.md](epic-4-atendimento.md) | F3 | S-14 a S-18 |
| E5 Integração WL | [epic-5-integracao-wl.md](epic-5-integracao-wl.md) | F4 | S-19 a S-22 |
| E6 CRM | [epic-6-crm.md](epic-6-crm.md) | F5 | S-23 a S-27 |
| E7 Campanhas | [epic-7-campanhas.md](epic-7-campanhas.md) | F6 | S-28 a S-31 |
| E8 Configuração | [epic-8-configuracao.md](epic-8-configuracao.md) | *proposto: pré-F7* | S-32 a S-34 |
| E9 Operação | [epic-9-operacao.md](epic-9-operacao.md) | *proposto: F7* | S-35, S-36 |

## Atenção — mapeamento F×E não é 1:1

O PRD define 8 fases (F0–F7) em §25.1 e 9 épicos (E1–E9) em §25.2. F0–F6 mapeiam 1:1 com E1–E7. **F7 (Piloto) não tem épico próprio** — o mapeamento de E8 e E9 para "adjacente/alinhado a F7" é uma proposta deste levantamento, não uma definição literal do PRD. Validar com o usuário antes de assumir como sequência de execução.

## Dependência sequencial explícita do PRD

> "F2 precede F3: o motor de IA depende do contexto de identificação para funcionar corretamente." (§25.1)

Ou seja: **E3 bloqueia E4**, formalmente, não por inferência.

## Gates abertos (bloqueiam início de desenvolvimento das stories indicadas)

| Gate | Bloqueia | Responsável |
|---|---|---|
| Estratégia de deploy Cloud Run → VPS ausente do PRD §24 | S-35, S-36 (E9) | @po |
| Q8 — modelo de LLM (NFR11) | S-15 (E4) | Optus Agent |
| Q1, Q2, Q3 — contrato WebLocação | S-20, S-21 (E5) | WebLocação (externo) |
| S-03 e S-34 sem AC formal na matriz §26 | S-03 (E1), S-34 (E8) | @po, ao validar a story |

## Config

`core-config.yaml` foi atualizado para refletir a realidade do projeto:
- `prd.prdFile: PRD-ALFAIA-v2.md` (fonte monolítica, na raiz — não `docs/prd.md`)
- `prd.prdSharded: true`, `prd.prdShardedLocation: docs/prd` (este diretório)
- `prd.epicFilePattern: epic-{n}*.md` (já era o padrão, agora satisfeito)

## Nota operacional

O banco Supabase (`irewoqkwywsapiiytdau`) está ativo e vazio (schema `public` sem tabelas) — pronto para a migration de S-01. O histórico de migrations do projeto já contém duas migrations de teste de conectividade (`create_connection_test_table`, `drop_connection_test_table`), sem impacto em schema — não é sujeira a limpar, apenas não estranhar ao rodar `list_migrations`.

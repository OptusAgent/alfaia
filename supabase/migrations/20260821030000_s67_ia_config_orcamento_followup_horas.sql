-- Migration Story 6.7: janela específica de follow-up para leads parados em 'orcamento' (PRD §9.7/§10.2, AC 3, 6)
-- Distinta de `janela_silencio_horas` (24h, usada para qualificando/negociando) — o usuário definiu
-- explicitamente 78h como a janela de leads em orçamento frio, e ela precisa ser parametrizável por tenant.

alter table ia_config
  add column if not exists orcamento_followup_horas int not null default 78
    check (orcamento_followup_horas between 1 and 720);

comment on column ia_config.orcamento_followup_horas is
  'Horas sem resposta em status ''orcamento'' até mover automaticamente para ''follow_up''. Default 78h (decisão de produto, story 6.7). Distinta de janela_silencio_horas (24h, cobre qualificando/negociando).';

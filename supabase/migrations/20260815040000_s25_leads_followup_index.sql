-- Migration Story 6.4: Índice parcial de alta performance para o worker de follow-up (PRD §17.4, Task 1)

create index if not exists leads_followup on leads(tenant_id, followup_proximo_em)
  where status in ('orcamento','qualificando','negociando','follow_up');

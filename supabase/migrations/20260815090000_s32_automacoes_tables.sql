-- Migration Story 8.2: Tabelas de automações, toggles e histórico de execuções (PRD §16, §17.8, Task 1)

create table if not exists automacoes (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  chave text not null,
  ativo boolean not null default true,
  criado_em timestamptz not null default now(),
  unique (tenant_id, chave)
);

create table if not exists automacao_execucoes (
  id bigserial primary key,
  tenant_id uuid not null references tenants(id) on delete cascade,
  chave text not null,
  lead_id uuid references leads(id),
  entrada text,
  resultado text,
  latencia_ms int,
  erro text,
  executado_em timestamptz not null default now()
);

create index if not exists automacoes_tenant on automacoes(tenant_id, chave);
create index if not exists automacao_execucoes_tenant on automacao_execucoes(tenant_id, chave, executado_em desc);

alter table automacoes enable row level security;
alter table automacao_execucoes enable row level security;

-- Políticas de RLS por pertencimento de tenant (PRD §17.11)
create policy automacoes_tenant on automacoes for all
  using (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()))
  with check (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()));

create policy automacao_execucoes_tenant on automacao_execucoes for all
  using (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()))
  with check (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()));

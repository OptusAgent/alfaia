-- Migration Story 5.3: Tabela de agendamentos e idempotência de escritas na WebLocação (PRD §17.7, I6)

create table if not exists agendamentos (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  wl_agendamento_id text,
  lead_id uuid references leads(id) on delete set null,
  tipo text not null,
  data date not null,
  hora time not null,
  cliente_nome text,
  cliente_telefone text,
  produto_ref text,
  origem text not null default 'automacao',
  status text not null default 'ativo',
  sincronizado_em timestamptz not null default now(),
  unique (tenant_id, wl_agendamento_id)
);

-- Índice único parcial que assegura a regra de escrita idempotente por (tenant_id, lead_id, data, hora) (I6, AC 2)
create unique index if not exists agendamentos_idempotencia on agendamentos(tenant_id, lead_id, data, hora)
  where status = 'ativo';

create index if not exists agendamentos_tenant_lead on agendamentos(tenant_id, lead_id);
alter table agendamentos enable row level security;

-- Políticas de RLS por pertencimento de tenant (PRD §17.11)
create policy agendamentos_tenant on agendamentos for all
  using (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()))
  with check (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()));

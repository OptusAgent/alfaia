-- Migration Story 7.3: Tabela de campanhas de reengajamento e disparo em massa (PRD §17.8, Task 4)

create table if not exists campanhas (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  nome text not null,
  segmento jsonb not null,
  mensagem_id uuid references mensagens_followup(id),
  status text not null default 'rascunho',
  agendada_para timestamptz,
  total int not null default 0,
  enviados int not null default 0,
  falhas int not null default 0,
  respondidos int not null default 0,
  pausada_motivo text,
  criado_em timestamptz not null default now()
);

create index if not exists campanhas_tenant on campanhas(tenant_id, status);
alter table campanhas enable row level security;

-- Políticas de RLS por pertencimento de tenant (PRD §17.11)
create policy campanhas_tenant on campanhas for all
  using (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()))
  with check (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()));

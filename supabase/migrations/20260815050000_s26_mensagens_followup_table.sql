-- Migration Story 6.5: Tabela de mensagens cadastradas de follow-up (PRD §17.8, AC 1, AC 2)

create table if not exists mensagens_followup (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  nome text not null,
  corpo text not null,
  template_meta text,
  ativa boolean not null default true
);

create index if not exists mensagens_followup_tenant on mensagens_followup(tenant_id);
alter table mensagens_followup enable row level security;

-- Políticas de RLS por pertencimento de tenant (PRD §17.11)
create policy mensagens_followup_tenant on mensagens_followup for all
  using (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()))
  with check (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()));

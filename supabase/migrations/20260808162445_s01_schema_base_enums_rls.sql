-- Story 1.1 (PRD S-01): Schema base, enums e RLS
-- Fonte literal: PRD-ALFAIA-v2.md §17.1, §17.2, §17.11
-- Aplicada via Supabase MCP em 2026-08-08 (project irewoqkwywsapiiytdau)

create type lead_status as enum (
  'novo','qualificando','orcamento','follow_up','negociando','agendado','ganho','descartado'
);
create type lead_origem as enum (
  'whatsapp_organico','instagram','indicacao','google','campanha','manual'
);
create type canal_provider as enum ('uazapi','meta');
create type remetente as enum ('lead','ia','atendente','sistema');
create type conversa_estado as enum ('ia','humano','pausada','transbordo');
create type tipo_entrada as enum ('primeiro_contato','continuacao','retomada','reengajamento');

create table tenants (
  id uuid primary key default gen_random_uuid(),
  nome text not null,
  slug text unique not null,
  cidade text, uf text,
  ativo boolean not null default true,
  criado_em timestamptz not null default now()
);

create table tenant_membros (
  tenant_id uuid not null references tenants(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  papel text not null default 'atendente' check (papel in ('dono','atendente','operador')),
  primary key (tenant_id, user_id)
);

alter table tenants enable row level security;
alter table tenant_membros enable row level security;

-- tenants: um usuario le apenas os tenants dos quais e membro
create policy tenants_tenant on tenants for select
  using (id in (select tenant_id from tenant_membros where user_id = auth.uid()));

-- tenant_membros: padrao de pertencimento (§17.11), aplicado aqui as duas tabelas fundacionais
create policy tenant_membros_tenant on tenant_membros for all
  using (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()))
  with check (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()));

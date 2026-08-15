-- Migration Story 5.1: Tabelas de integração WebLocação (WL) e auditoria de chamadas (PRD §17.7)

-- 1. Tabela de configuração da integração WL por tenant (PRD §17.7, I1, I8)
create table if not exists wl_integracao (
  tenant_id uuid primary key references tenants(id) on delete cascade,
  base_url text not null,
  api_key text not null, -- Criptografada em repouso
  loja_ref text,
  modo text not null default 'mock',
  ativa boolean not null default true,
  ultimo_sync_em timestamptz
);
alter table wl_integracao enable row level security;

-- 2. Tabela de auditoria telemétrica de chamadas à API da WebLocação (PRD §17.7, I3)
create table if not exists wl_chamadas (
  id bigserial primary key,
  tenant_id uuid not null references tenants(id) on delete cascade,
  metodo text,
  rota text,
  status_code int,
  latencia_ms int,
  erro text,
  criado_em timestamptz not null default now()
);
create index if not exists wl_chamadas_tenant_data on wl_chamadas(tenant_id, criado_em desc);
alter table wl_chamadas enable row level security;

-- 3. Políticas de RLS por pertencimento de tenant (PRD §17.11)
create policy wl_integracao_tenant on wl_integracao for all
  using (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()))
  with check (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()));

create policy wl_chamadas_tenant on wl_chamadas for all
  using (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()))
  with check (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()));

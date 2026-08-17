-- S34: Dados operacionais da instancia UAZAPI no canal.

alter table canais
  add column if not exists telefone text,
  add column if not exists ultimo_healthcheck_em timestamptz,
  add column if not exists ultimo_status_raw jsonb,
  add column if not exists editado_em timestamptz not null default now(),
  add column if not exists excluido_em timestamptz;

create unique index if not exists canais_tenant_instancia_unique
  on canais(tenant_id, uazapi_instancia)
  where uazapi_instancia is not null and excluido_em is null;

create index if not exists canais_tenant_status
  on canais(tenant_id, status, ativo)
  where excluido_em is null;

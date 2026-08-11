-- Migration Story 2.3: Tabela de canais e índice de garantia de canal único ativo por tenant (PRD §17.3, §14.3)

create table if not exists canais (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  provider canal_provider not null,
  nome text not null,
  ativo boolean not null default false,
  uazapi_base_url text,
  uazapi_instancia text,
  uazapi_token text,
  status text default 'desconectado',
  qualidade text,
  aquecimento_iniciado_em date,
  criado_em timestamptz not null default now()
);

alter table canais enable row level security;

-- Garantia de no máximo um canal ativo por tenant
create unique index if not exists canais_um_ativo on canais(tenant_id) where ativo;

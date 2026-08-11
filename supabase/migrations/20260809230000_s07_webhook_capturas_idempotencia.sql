-- Migration Story 2.2: Tabela de capturas brutas de webhook e índice de idempotência por wa_message_id (PRD §17.3, §17.5)

create table if not exists webhook_capturas (
  id bigserial primary key,
  tenant_id uuid references tenants(id) on delete set null,
  provider canal_provider,
  metodo text,
  url text,
  headers jsonb,
  corpo text,
  hmac_ok boolean,
  criado_em timestamptz not null default now()
);

alter table webhook_capturas enable row level security;

-- Estrutura base da tabela de mensagens e índice de idempotência único parcial
create table if not exists mensagens (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  canal_id uuid references canais(id) on delete set null,
  wa_message_id text,
  de_mim boolean not null default false,
  telefone text not null,
  conteudo text,
  midia_url text,
  midia_tipo text default 'text',
  status text default 'recebido',
  criado_em timestamptz not null default now()
);

alter table mensagens enable row level security;

create unique index if not exists mensagens_wamid on mensagens(wa_message_id) where wa_message_id is not null;

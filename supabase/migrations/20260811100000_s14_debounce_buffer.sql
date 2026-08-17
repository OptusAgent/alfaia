-- Migration Story 4.1: Tabelas de conversas, mensagens e debounce_buffer com SKIP LOCKED (PRD §17.5, §17.6)

-- 1. Tabela de conversas por contato (PRD §17.5)
create table if not exists conversas (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  contato_id uuid not null references contatos(id) on delete cascade,
  lead_id uuid references leads(id) on delete set null,
  canal_id uuid references canais(id) on delete set null,
  estado conversa_estado not null default 'ia',
  resumo text,
  pausada_em timestamptz,
  ativada_em timestamptz,
  criada_em timestamptz not null default now(),
  unique (tenant_id, contato_id)
);
create index if not exists conversas_tenant_contato on conversas(tenant_id, contato_id);
alter table conversas enable row level security;

-- 2. Tabela de histórico de mensagens da conversa (PRD §17.5)
create table if not exists mensagens (
  id bigserial primary key,
  tenant_id uuid not null references tenants(id) on delete cascade,
  conversa_id uuid not null references conversas(id) on delete cascade,
  lead_id uuid references leads(id) on delete set null,
  wa_message_id text,
  remetente remetente not null default 'lead',
  texto text,
  midia_url text,
  midia_tipo text,
  payload jsonb,
  enviado_em timestamptz not null default now()
);
create index if not exists mensagens_wamid on mensagens(wa_message_id)
  where wa_message_id is not null;
create index if not exists mensagens_conversa_history on mensagens(conversa_id, enviado_em desc);
alter table mensagens enable row level security;

-- 3. Tabela de buffer de debounce para agrupamento de mensagens (PRD §17.6)
create table if not exists debounce_buffer (
  id bigserial primary key,
  tenant_id uuid not null references tenants(id) on delete cascade,
  conversa_id uuid not null references conversas(id) on delete cascade,
  processar_em timestamptz not null,
  bloqueado_em timestamptz,
  criado_em timestamptz not null default now()
);

-- Índice único parcial que assegura no máximo um registro de debounce não bloqueado por conversa
create unique index if not exists debounce_um_por_conversa on debounce_buffer(conversa_id)
  where bloqueado_em is null;

create index if not exists debounce_processar on debounce_buffer(processar_em)
  where bloqueado_em is null;
alter table debounce_buffer enable row level security;

-- 4. Políticas de RLS por pertencimento de tenant (PRD §17.11)
create policy conversas_tenant on conversas for all
  using (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()))
  with check (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()));

create policy mensagens_tenant on mensagens for all
  using (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()))
  with check (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()));

create policy debounce_buffer_tenant on debounce_buffer for all
  using (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()))
  with check (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()));

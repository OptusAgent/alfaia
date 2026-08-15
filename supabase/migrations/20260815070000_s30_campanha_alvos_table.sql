-- Migration Story 7.4: Tabela de alvos de campanha e rastreamento de disparos (PRD §17.8, Task 1)

create table if not exists campanha_alvos (
  id bigserial primary key,
  campanha_id uuid not null references campanhas(id) on delete cascade,
  contato_id uuid not null references contatos(id) on delete cascade,
  status text not null default 'pendente',
  wa_message_id text,
  enviado_em timestamptz,
  unique (campanha_id, contato_id)
);

create index if not exists campanha_alvos_campanha on campanha_alvos(campanha_id, status);
alter table campanha_alvos enable row level security;

-- Políticas de RLS por pertencimento de tenant via campanha (PRD §17.11)
create policy campanha_alvos_tenant on campanha_alvos for all
  using (campanha_id in (select id from campanhas where tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid())))
  with check (campanha_id in (select id from campanhas where tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid())));

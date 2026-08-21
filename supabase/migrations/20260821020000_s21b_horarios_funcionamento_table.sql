-- Achado real em produção (2026-08-21, story 5.3): consultar_slots devolvia 4 horários fixos
-- (09:00, 11:00, 14:00, 16:00) sempre, sem nenhum conceito de horário de funcionamento real da
-- loja — nem por dia da semana, nem por turno (manhã/tarde). horario_comercial em ia_config é um
-- conceito diferente (janela anti-spam para disparo de campanha, story 7.x) e não serve para isto.
--
-- Tabela nova e própria: horário de funcionamento real da loja, usado por consultar_slots para
-- nunca oferecer um horário fora do expediente. Suporta múltiplos turnos por dia (ex.: manhã e
-- tarde) e é editável por tenant (CRUD de portal fica para story futura — ver Dev Notes).

create table if not exists horarios_funcionamento (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  -- 0=domingo, 1=segunda, ..., 6=sábado (mesma convenção de extract(dow from timestamp))
  dia_semana smallint not null check (dia_semana between 0 and 6),
  hora_abertura time not null,
  hora_fechamento time not null,
  ativo boolean not null default true,
  criado_em timestamptz not null default now(),
  editado_em timestamptz not null default now(),
  constraint horarios_funcionamento_intervalo_valido check (hora_fechamento > hora_abertura)
);

create index if not exists horarios_funcionamento_tenant_dia_idx
  on horarios_funcionamento(tenant_id, dia_semana)
  where ativo;

alter table horarios_funcionamento enable row level security;

create policy horarios_funcionamento_tenant on horarios_funcionamento for all
  using (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()))
  with check (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()));

comment on table horarios_funcionamento is
  'Horário de funcionamento real da loja para agendamento (provas/retiradas) — nunca confundir com ia_config.horario_comercial (janela anti-spam de campanha, story 7.x). Um tenant pode ter múltiplas linhas por dia_semana (turnos).';

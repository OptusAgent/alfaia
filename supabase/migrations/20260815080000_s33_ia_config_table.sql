-- Migration Story 8.1: Tabela de configurações da IA por tenant (PRD §17.9, Task 4)

create table if not exists ia_config (
  tenant_id uuid primary key references tenants(id) on delete cascade,
  persona_nome text not null default 'Atendente da Alfaia',
  prompt_sistema text not null default 'Você é a atendente virtual da Alfaia Alta Costura. Seu tom é elegante, acolhedor e atencioso.',
  modelo text not null default 'claude-sonnet-4-6',
  temperatura numeric(2,1) not null default 0.3,
  janela_retomada_dias int not null default 7 check (janela_retomada_dias between 1 and 90),
  janela_silencio_horas int not null default 24,
  max_tentativas_followup int not null default 3,
  intervalo_tentativas_horas int not null default 48,
  disparo_followup_automatico boolean not null default false,
  pausa_transbordo_minutos int not null default 30,
  horario_comercial jsonb not null default '{"inicio":"09:00","fim":"18:00","dias":[1,2,3,4,5,6]}'::jsonb
);

alter table ia_config enable row level security;

-- Políticas de RLS por pertencimento de tenant (PRD §17.11)
create policy ia_config_tenant on ia_config for all
  using (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()))
  with check (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()));

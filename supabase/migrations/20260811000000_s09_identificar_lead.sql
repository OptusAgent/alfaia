-- Migration Story 3.1: Tabelas de contatos, leads e função atômica identificar_lead (PRD §17.4, §17.9, §17.10)

-- 1. Tabela de configuração de IA por tenant (PRD §17.9)
create table if not exists ia_config (
  tenant_id uuid primary key references tenants(id) on delete cascade,
  persona_nome text not null default 'Atendente',
  prompt_sistema text not null default 'Você é a assistente de atendimento do ALFAIA.',
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

-- 2. Tabela de contatos (PRD §17.4)
create table if not exists contatos (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  telefone text not null,
  nome text,
  tags jsonb not null default '{}'::jsonb,
  opt_out boolean not null default false,
  opt_out_em timestamptz,
  opt_out_revertido_em timestamptz,
  total_leads int not null default 0,
  primeiro_contato_em timestamptz not null default now(),
  ultimo_contato_em timestamptz,
  criado_em timestamptz not null default now(),
  unique (tenant_id, telefone)
);
create index if not exists contatos_tel on contatos(tenant_id, telefone);
alter table contatos enable row level security;

-- 3. Tabela de leads (PRD §17.4)
create table if not exists leads (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  contato_id uuid not null references contatos(id) on delete cascade,
  lead_seq int not null default 1,
  status lead_status not null default 'novo',
  origem lead_origem not null default 'whatsapp_organico',
  evento_tipo text,
  evento_data date,
  papel text,
  peca_interesse text,
  tamanho text,
  cor text,
  valor_estimado numeric(10,2),
  followup_tentativas int not null default 0,
  followup_proximo_em timestamptz,
  reaberto_em timestamptz,
  reaberto_de_lead_id uuid references leads(id) on delete set null,
  status_alterado_em timestamptz not null default now(),
  status_alterado_por remetente not null default 'sistema',
  motivo_descarte text,
  ganho_em timestamptz,
  ultimo_contato_em timestamptz not null default now(),
  atualizado_em timestamptz not null default now(),
  criado_em timestamptz not null default now(),
  unique (contato_id, lead_seq)
);
create index if not exists leads_board on leads(tenant_id, status, atualizado_em desc);
create index if not exists leads_followup on leads(tenant_id, followup_proximo_em)
  where status in ('orcamento','qualificando','negociando','follow_up');
create index if not exists leads_contato_atual on leads(contato_id, criado_em desc);
alter table leads enable row level security;

-- 4. Histórico de interesses (PRD §17.4)
create table if not exists lead_interesses (
  id bigserial primary key,
  tenant_id uuid not null references tenants(id) on delete cascade,
  lead_id uuid not null references leads(id) on delete cascade,
  versao int not null default 1,
  evento_tipo text, evento_data date, papel text,
  peca_interesse text, tamanho text, cor text,
  valor_estimado numeric(10,2),
  motivo text,
  criado_em timestamptz not null default now(),
  unique (lead_id, versao)
);
alter table lead_interesses enable row level security;

-- 5. Tabela de eventos e auditoria do lead (PRD §17.4)
create table if not exists lead_eventos (
  id bigserial primary key,
  tenant_id uuid not null references tenants(id) on delete cascade,
  lead_id uuid not null references leads(id) on delete cascade,
  tipo text not null,
  de text, para text,
  autor remetente not null default 'sistema',
  autor_user_id uuid references auth.users(id),
  motivo text,
  detalhe jsonb,
  criado_em timestamptz not null default now()
);
create index if not exists lead_eventos_lead on lead_eventos(lead_id, criado_em desc);
alter table lead_eventos enable row level security;

-- 6. Políticas de RLS por pertencimento de tenant (PRD §17.11)
create policy ia_config_tenant on ia_config for all
  using (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()))
  with check (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()));

create policy contatos_tenant on contatos for all
  using (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()))
  with check (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()));

create policy leads_tenant on leads for all
  using (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()))
  with check (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()));

create policy lead_interesses_tenant on lead_interesses for all
  using (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()))
  with check (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()));

create policy lead_eventos_tenant on lead_eventos for all
  using (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()))
  with check (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()));

-- 7. Função de Identificação de Lead Atômica (PRD §17.10, §9.4, AC 9.1-9.4)
create or replace function identificar_lead(
  p_tenant uuid,
  p_telefone text,
  p_push_name text,
  p_origem lead_origem default 'whatsapp_organico'
) returns table (contato_id uuid, lead_id uuid, entrada tipo_entrada)
language plpgsql as $$
declare
  v_contato uuid;
  v_lead uuid;
  v_status lead_status;
  v_ultimo timestamptz;
  v_seq int;
  v_janela int;
  v_opt_out boolean;
  v_entrada tipo_entrada;
begin
  -- Busca a janela de retomada personalizada em dias da tabela ia_config (padrão: 7 dias)
  select janela_retomada_dias into v_janela from ia_config where tenant_id = p_tenant;
  v_janela := coalesce(v_janela, 7);

  -- 1. Insere ou atualiza o contato atomicamente (evita race condition sob alta concorrência)
  insert into contatos (tenant_id, telefone, nome)
  values (p_tenant, p_telefone, p_push_name)
  on conflict (tenant_id, telefone) do update
    set ultimo_contato_em = now(),
        nome = coalesce(contatos.nome, excluded.nome)
  returning id, opt_out into v_contato, v_opt_out;

  -- Reversão automática de opt-out caso o cliente envie mensagem ativamente
  if v_opt_out is true then
    update contatos
      set opt_out = false,
          opt_out_revertido_em = now()
      where id = v_contato;
  end if;

  -- 2. Busca o último lead registrado para este contato
  select id, status, ultimo_contato_em, lead_seq
    into v_lead, v_status, v_ultimo, v_seq
  from leads
  where contato_id = v_contato
  order by criado_em desc
  limit 1;

  -- 3. Aplica a Matriz de Decisão do PRD §9.4
  if v_lead is null then
    v_entrada := 'primeiro_contato';
  elsif v_opt_out is true or v_status in ('ganho', 'descartado') then
    v_entrada := 'reengajamento';
  elsif now() - v_ultimo >= (v_janela || ' days')::interval then
    v_entrada := 'retomada';
  else
    v_entrada := 'continuacao';
  end if;

  -- Se for um novo lead (primeiro contato ou reengajamento após encerramento)
  if v_entrada in ('primeiro_contato', 'reengajamento') then
    insert into leads (tenant_id, contato_id, lead_seq, origem, reaberto_de_lead_id)
    values (
      p_tenant,
      v_contato,
      coalesce(v_seq, 0) + 1,
      p_origem,
      case when v_entrada = 'reengajamento' then v_lead else null end
    )
    returning id into v_lead;

    update contatos set total_leads = total_leads + 1 where id = v_contato;

    -- Auditoria na linha do tempo
    insert into lead_eventos (tenant_id, lead_id, tipo, para, autor, detalhe)
    values (
      p_tenant,
      v_lead,
      'lead_criado',
      'novo',
      'sistema',
      jsonb_build_object('entrada', v_entrada, 'opt_out_revertido', v_opt_out)
    );
  else
    -- Continuação ou Retomada do lead existente
    update leads
      set ultimo_contato_em = now(),
          reaberto_em = case when v_entrada = 'retomada' then now() else reaberto_em end
      where id = v_lead;

    if v_entrada = 'retomada' then
      insert into lead_eventos (tenant_id, lead_id, tipo, autor, detalhe)
      values (
        p_tenant,
        v_lead,
        'reaberto',
        'sistema',
        jsonb_build_object('dias_silencio', extract(day from now() - v_ultimo))
      );
    end if;
  end if;

  return query select v_contato, v_lead, v_entrada;
end $$;

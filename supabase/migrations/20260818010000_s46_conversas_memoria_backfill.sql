-- Story 4.6: Persistência real de conversas, memória Postgres e reset de testes

alter table mensagens add column if not exists conversa_id uuid references conversas(id) on delete cascade;
alter table mensagens add column if not exists lead_id uuid references leads(id) on delete set null;
alter table mensagens add column if not exists remetente remetente not null default 'lead';
alter table mensagens add column if not exists texto text;
alter table mensagens add column if not exists payload jsonb;
alter table mensagens add column if not exists enviado_em timestamptz not null default now();
alter table mensagens add column if not exists telefone text;
alter table mensagens add column if not exists conteudo text;
alter table mensagens add column if not exists de_mim boolean not null default false;
alter table mensagens add column if not exists status text default 'recebido';
alter table mensagens add column if not exists canal_id uuid references canais(id) on delete set null;
alter table mensagens add column if not exists criado_em timestamptz not null default now();

create index if not exists mensagens_conversa_history on mensagens(conversa_id, enviado_em desc);
create index if not exists mensagens_tenant_telefone on mensagens(tenant_id, telefone, enviado_em desc);

create table if not exists memoria_reset_auditoria (
  id bigserial primary key,
  tenant_id uuid not null references tenants(id) on delete cascade,
  user_id uuid references auth.users(id) on delete set null,
  telefone text,
  escopo text not null default 'tenant',
  mensagens_removidas int not null default 0,
  conversas_removidas int not null default 0,
  leads_removidos int not null default 0,
  contatos_removidos int not null default 0,
  motivo text,
  criado_em timestamptz not null default now()
);

alter table memoria_reset_auditoria enable row level security;

drop policy if exists memoria_reset_auditoria_tenant on memoria_reset_auditoria;
create policy memoria_reset_auditoria_tenant on memoria_reset_auditoria for all
  using (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()))
  with check (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()));

create or replace function registrar_mensagem_idempotente(p_payload jsonb)
returns void
language plpgsql
as $$
begin
  insert into mensagens (
    tenant_id, canal_id, conversa_id, lead_id, wa_message_id, remetente, texto,
    payload, enviado_em, de_mim, telefone, conteudo, midia_url, midia_tipo,
    status
  )
  values (
    (p_payload ->> 'tenant_id')::uuid,
    nullif(p_payload ->> 'canal_id', '')::uuid,
    nullif(p_payload ->> 'conversa_id', '')::uuid,
    nullif(p_payload ->> 'lead_id', '')::uuid,
    nullif(p_payload ->> 'wa_message_id', ''),
    coalesce(nullif(p_payload ->> 'remetente', ''), 'lead')::remetente,
    p_payload ->> 'texto',
    p_payload -> 'payload',
    coalesce(nullif(p_payload ->> 'enviado_em', '')::timestamptz, now()),
    coalesce((p_payload ->> 'de_mim')::boolean, false),
    p_payload ->> 'telefone',
    p_payload ->> 'conteudo',
    p_payload ->> 'midia_url',
    coalesce(nullif(p_payload ->> 'midia_tipo', ''), 'text'),
    coalesce(nullif(p_payload ->> 'status', ''), 'recebido')
  )
  on conflict (wa_message_id) where wa_message_id is not null do nothing;
end $$;

create or replace function backfill_conversas_memoria()
returns table (mensagens_atualizadas int, capturas_importadas int)
language plpgsql
as $$
declare
  r record;
  v_contato uuid;
  v_lead uuid;
  v_entrada tipo_entrada;
  v_conversa uuid;
  v_telefone text;
  v_nome text;
  v_texto text;
  v_wamid text;
  v_payload jsonb;
  v_tenant uuid;
  v_canal uuid;
  v_instancia text;
  v_base_url text;
  v_candidatos int;
begin
  mensagens_atualizadas := 0;
  capturas_importadas := 0;

  for r in
    select *
    from mensagens
    where conversa_id is null
      and tenant_id is not null
      and telefone is not null
  loop
    select contato_id, lead_id, entrada
      into v_contato, v_lead, v_entrada
    from identificar_lead(r.tenant_id, r.telefone, 'Cliente WhatsApp', 'whatsapp_organico');

    insert into conversas (tenant_id, contato_id, lead_id, canal_id, estado, ativada_em)
    values (r.tenant_id, v_contato, v_lead, r.canal_id, 'ia', now())
    on conflict (tenant_id, contato_id) do update
      set lead_id = coalesce(conversas.lead_id, excluded.lead_id),
          canal_id = coalesce(excluded.canal_id, conversas.canal_id),
          ativada_em = now()
    returning id into v_conversa;

    update mensagens
      set conversa_id = v_conversa,
          lead_id = coalesce(r.lead_id, v_lead),
          remetente = case when coalesce(r.de_mim, false) then 'ia'::remetente else 'lead'::remetente end,
          texto = coalesce(r.texto, r.conteudo),
          enviado_em = coalesce(r.enviado_em, r.criado_em, now())
      where id = r.id;

    mensagens_atualizadas := mensagens_atualizadas + 1;
  end loop;

  for r in
    select c.*
    from webhook_capturas c
    where c.provider = 'uazapi'
      and c.corpo is not null
      and c.corpo ~ '^\s*\{'
  loop
    begin
      v_payload := r.corpo::jsonb;
      v_telefone := regexp_replace(coalesce(v_payload #>> '{message,chatid}', ''), '\D', '', 'g');
      v_texto := coalesce(v_payload #>> '{message,text}', v_payload #>> '{message,content}');
      v_wamid := coalesce(v_payload #>> '{message,messageid}', v_payload #>> '{message,id}');
      v_nome := coalesce(v_payload #>> '{message,senderName}', v_payload #>> '{chat,name}', 'Cliente WhatsApp');
      v_instancia := coalesce(
        v_payload ->> 'InstanceName',
        v_payload ->> 'instanceName',
        v_payload ->> 'instance',
        v_payload #>> '{instance,name}',
        v_payload #>> '{Instance,Name}'
      );
      v_base_url := coalesce(v_payload ->> 'BaseUrl', v_payload ->> 'baseUrl');
      v_tenant := r.tenant_id;
      v_canal := null;

      if v_tenant is not null then
        select id
          into v_canal
        from canais
        where tenant_id = v_tenant
          and provider = 'uazapi'
          and excluido_em is null
        order by ativo desc, criado_em desc
        limit 1;
      end if;

      if v_tenant is null then
        select id, tenant_id
          into v_canal, v_tenant
        from canais
        where provider = 'uazapi'
          and excluido_em is null
          and (
            (v_instancia is not null and uazapi_instancia = v_instancia)
            or (v_base_url is not null and rtrim(coalesce(uazapi_base_url, ''), '/') = rtrim(v_base_url, '/'))
          )
        order by ativo desc, criado_em desc
        limit 1;
      end if;

      if v_tenant is null then
        select count(*), max(id), max(tenant_id)
          into v_candidatos, v_canal, v_tenant
        from canais
        where provider = 'uazapi'
          and ativo is true
          and excluido_em is null;

        if v_candidatos <> 1 then
          raise warning 'backfill_conversas_memoria: captura % sem tenant resolvivel; candidatos=%', r.id, v_candidatos;
          continue;
        end if;
      end if;

      if v_telefone is null or length(v_telefone) < 10 or v_texto is null or v_texto = '' then
        continue;
      end if;
      if length(v_telefone) in (10, 11) and left(v_telefone, 2) <> '55' then
        v_telefone := '55' || v_telefone;
      end if;

      select contato_id, lead_id, entrada
        into v_contato, v_lead, v_entrada
      from identificar_lead(v_tenant, v_telefone, v_nome, 'whatsapp_organico');

      insert into conversas (tenant_id, contato_id, lead_id, canal_id, estado, ativada_em)
      values (v_tenant, v_contato, v_lead, v_canal, 'ia', now())
      on conflict (tenant_id, contato_id) do update
        set lead_id = coalesce(conversas.lead_id, excluded.lead_id),
            canal_id = coalesce(excluded.canal_id, conversas.canal_id),
            ativada_em = now()
      returning id into v_conversa;

      perform registrar_mensagem_idempotente(jsonb_build_object(
        'tenant_id', v_tenant,
        'canal_id', v_canal,
        'conversa_id', v_conversa,
        'lead_id', v_lead,
        'wa_message_id', coalesce(v_wamid, 'captura-' || r.id::text),
        'remetente', 'lead',
        'texto', v_texto,
        'payload', v_payload,
        'enviado_em', r.criado_em,
        'telefone', v_telefone,
        'conteudo', v_texto,
        'de_mim', false,
        'status', 'recebido'
      ));

      capturas_importadas := capturas_importadas + 1;
    exception when invalid_text_representation then
      raise warning 'backfill_conversas_memoria: captura % com JSON invalido ou cast invalido', r.id;
      continue;
    exception when others then
      raise warning 'backfill_conversas_memoria: captura % falhou: %', r.id, sqlerrm;
      continue;
    end;
  end loop;

  return next;
end $$;

select * from backfill_conversas_memoria();

-- Story 4.6: corrige ambiguidade real da RPC identificar_lead antes do backfill.

create or replace function identificar_lead(
  p_tenant uuid,
  p_telefone text,
  p_push_name text,
  p_origem lead_origem default 'whatsapp_organico'
) returns table (contato_id uuid, lead_id uuid, entrada tipo_entrada)
language plpgsql
as $$
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
  select ic.janela_retomada_dias
    into v_janela
  from ia_config ic
  where ic.tenant_id = p_tenant;
  v_janela := coalesce(v_janela, 7);

  insert into contatos (tenant_id, telefone, nome)
  values (p_tenant, p_telefone, p_push_name)
  on conflict (tenant_id, telefone) do update
    set ultimo_contato_em = now(),
        nome = coalesce(contatos.nome, excluded.nome)
  returning id, opt_out into v_contato, v_opt_out;

  if v_opt_out is true then
    update contatos c
      set opt_out = false,
          opt_out_revertido_em = now()
      where c.id = v_contato;
  end if;

  select l.id, l.status, l.ultimo_contato_em, l.lead_seq
    into v_lead, v_status, v_ultimo, v_seq
  from leads l
  where l.contato_id = v_contato
  order by l.criado_em desc
  limit 1;

  if v_lead is null then
    v_entrada := 'primeiro_contato';
  elsif v_opt_out is true or v_status in ('ganho', 'descartado') then
    v_entrada := 'reengajamento';
  elsif now() - v_ultimo >= (v_janela || ' days')::interval then
    v_entrada := 'retomada';
  else
    v_entrada := 'continuacao';
  end if;

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

    update contatos c
      set total_leads = total_leads + 1
      where c.id = v_contato;

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
    update leads l
      set ultimo_contato_em = now(),
          reaberto_em = case when v_entrada = 'retomada' then now() else l.reaberto_em end
      where l.id = v_lead;

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
end;
$$;

-- S35: Policies RLS do card de canais e modelo IA padrao OpenRouter.

alter table ia_config
  alter column modelo set default 'deepseek/deepseek-r1-distill-llama-70b';

update ia_config
set modelo = 'deepseek/deepseek-r1-distill-llama-70b'
where modelo is null
   or modelo = 'claude-sonnet-4-6';

insert into ia_config (tenant_id)
select id from tenants
on conflict (tenant_id) do nothing;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename = 'canais'
      and policyname = 'canais_tenant_select'
  ) then
    create policy canais_tenant_select on canais for select
      using (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()));
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename = 'canais'
      and policyname = 'canais_tenant_insert'
  ) then
    create policy canais_tenant_insert on canais for insert
      with check (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()));
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename = 'canais'
      and policyname = 'canais_tenant_update'
  ) then
    create policy canais_tenant_update on canais for update
      using (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()))
      with check (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()));
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename = 'canais'
      and policyname = 'canais_tenant_delete'
  ) then
    create policy canais_tenant_delete on canais for delete
      using (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()));
  end if;
end $$;

notify pgrst, 'reload schema';

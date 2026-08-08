-- Story 1.1 (PRD S-01): segunda correcao, encontrada pelo Supabase security
-- advisor (get_advisors) apos a correcao da recursao.
--
-- A funcao public.current_tenant_ids() (SECURITY DEFINER) ficava exposta
-- como endpoint RPC publico (/rest/v1/rpc/current_tenant_ids) simplesmente
-- por estar no schema "public", que o PostgREST expoe automaticamente.
-- A funcao so deveria ser chamada internamente pela policy de RLS, nunca
-- diretamente por um cliente. Padrao de correcao: mover para um schema que
-- o PostgREST nao expoe (aqui, "private").
--
-- Resultado: get_advisors(security) passou de 2 WARN para 0 lints.

create schema if not exists private;

drop policy if exists tenant_membros_tenant on tenant_membros;
drop function if exists public.current_tenant_ids();

create function private.current_tenant_ids()
returns setof uuid
language sql
security definer
stable
set search_path = public
as $$
  select tenant_id from tenant_membros where user_id = auth.uid();
$$;

revoke all on function private.current_tenant_ids() from public;
grant execute on function private.current_tenant_ids() to authenticated;

create policy tenant_membros_tenant on tenant_membros for all
  using (tenant_id in (select private.current_tenant_ids()))
  with check (tenant_id in (select private.current_tenant_ids()));

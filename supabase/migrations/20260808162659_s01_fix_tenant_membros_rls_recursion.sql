-- Story 1.1 (PRD S-01): correcao encontrada durante o teste de RLS cross-tenant
--
-- A policy original de tenant_membros consultava a propria tenant_membros
-- dentro do seu USING/WITH CHECK. Isso causa recursao infinita em Postgres
-- (ERRO 42P17), porque avaliar a subconsulta reaplica a mesma policy RLS
-- sobre a mesma tabela, indefinidamente. Detectado ao rodar o teste de
-- isolamento cross-tenant exigido pelo AC 4 desta story — nao foi um erro
-- teorico, a policy original quebrava qualquer SELECT em tenant_membros.
--
-- Correcao padrao para RLS self-referencing: uma funcao SECURITY DEFINER
-- (que roda com os privilegios do dono da funcao, bypassando RLS na sua
-- propria subconsulta interna) resolve o conjunto de tenant_id do usuario
-- atual sem reacionar a policy de tenant_membros.
--
-- Toda tabela de dominio criada em stories futuras (leads, contatos, etc.)
-- deve preferir `public.current_tenant_ids()` a repetir o subselect cru,
-- tanto por consistencia quanto para evitar o mesmo problema caso a tabela
-- algum dia precise se autorreferenciar.

drop policy if exists tenant_membros_tenant on tenant_membros;

create or replace function public.current_tenant_ids()
returns setof uuid
language sql
security definer
stable
set search_path = public
as $$
  select tenant_id from tenant_membros where user_id = auth.uid();
$$;

create policy tenant_membros_tenant on tenant_membros for all
  using (tenant_id in (select public.current_tenant_ids()))
  with check (tenant_id in (select public.current_tenant_ids()));

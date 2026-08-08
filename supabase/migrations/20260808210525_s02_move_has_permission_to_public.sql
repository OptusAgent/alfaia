-- Story 1.2 (PRD S-02): correcao de decisao tomada nesta mesma story.
--
-- has_permission() foi colocada em "private" no momento em que foi criada,
-- seguindo por reflexo o mesmo padrao aplicado a current_tenant_ids() em
-- 1.1. Isso estava errado: current_tenant_ids() e um helper puramente
-- interno de RLS (nenhum motivo de negocio para o app chamar), mas
-- has_permission() e explicitamente descrita no PRD (§4.2) como usada
-- "nas policies de RLS E nos guards das rotas do portal" -- ou seja, ela
-- PRECISA ser chamavel via RPC pelo Next.js (route handlers rodam sobre o
-- cliente supabase-js, que so alcanca funcoes expostas pelo PostgREST no
-- schema "public"). Descoberto ao implementar a story 1.3 e tentar montar
-- o guard de rota do Portal.
--
-- O advisor de seguranca volta a acusar "SECURITY DEFINER function
-- publicly executable" para has_permission() -- aceito conscientemente
-- aqui: a funcao so responde "o usuario autenticado atual pode fazer X no
-- tenant Y", nunca vaza dado de outro usuario, e SO EXISTE para ser
-- chamada de fora (mesmo padrao de is_claims_admin() nos guias oficiais
-- do Supabase). current_tenant_ids() continua em private, sem mudanca.

drop function if exists private.has_permission(uuid, text, text);

create or replace function public.has_permission(p_tenant_id uuid, p_recurso text, p_acao text)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select coalesce(
    (
      select pp.permitido
      from tenant_membros tm
      join private.permissoes_papel pp on pp.papel = tm.papel
      where tm.tenant_id = p_tenant_id
        and tm.user_id = auth.uid()
        and pp.recurso = p_recurso
        and pp.acao = p_acao
    ),
    false
  );
$$;

revoke all on function public.has_permission(uuid, text, text) from public;
grant execute on function public.has_permission(uuid, text, text) to authenticated;

comment on function public.has_permission(uuid, text, text) is
  'Exposta de proposito via RPC (PostgREST): guards de rota do Portal chamam esta funcao. So responde sobre o proprio auth.uid() do chamador, nunca vaza dado de terceiros -- WARN do advisor de seguranca e esperado e aceito, nao e falha.';

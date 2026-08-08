-- Story 1.2 (PRD S-02): Auth, tenancy e RBAC
-- Matriz literal de PRD §4.2. Os identificadores recurso:acao seguem o
-- formato usado na tabela de rotas do Portal (§18.2: lead:read, lead:update,
-- followup:create, atendimento:read, atendimento:update, agenda:read,
-- agenda:update, produto:read, contato:read, campanha:create, canal:update,
-- automacao:update). Duas linhas de §4.2 nao tem rota correspondente em
-- §18.2 ainda ("Editar prompt e persona", "Exportar dados") -- usei os
-- identificadores mais previsiveis (ia_config:update, contato:export) e
-- deixei marcado para confirmar quando as stories 8.1 e 9.2 definirem as
-- rotas reais. "Descartar lead" tambem ganhou acao propria (lead:discard)
-- por ja ter rota dedicada em §18.2 (POST /leads/{id}/descartar), distinta
-- de lead:update.

create table private.permissoes_papel (
  papel text not null check (papel in ('dono','atendente','operador')),
  recurso text not null,
  acao text not null,
  permitido boolean not null,
  fonte_prd text,
  primary key (papel, recurso, acao)
);

revoke all on private.permissoes_papel from public;
grant select on private.permissoes_papel to authenticated;

insert into private.permissoes_papel (papel, recurso, acao, permitido, fonte_prd) values
('dono','lead','read', true, 'Ver pipeline e leads'),
('atendente','lead','read', true, 'Ver pipeline e leads'),
('operador','lead','read', true, 'Ver pipeline e leads'),
('dono','lead','update', true, 'Mover card / editar lead'),
('atendente','lead','update', true, 'Mover card / editar lead'),
('operador','lead','update', true, 'Mover card / editar lead'),
('dono','lead','discard', true, 'Descartar lead'),
('atendente','lead','discard', true, 'Descartar lead'),
('operador','lead','discard', true, 'Descartar lead'),
('dono','followup','create', true, 'Disparar follow-up'),
('atendente','followup','create', true, 'Disparar follow-up'),
('operador','followup','create', false, 'Disparar follow-up'),
('dono','atendimento','update', true, 'Assumir / devolver conversa'),
('atendente','atendimento','update', true, 'Assumir / devolver conversa'),
('operador','atendimento','update', true, 'Assumir / devolver conversa'),
('dono','campanha','create', true, 'Criar e disparar campanha'),
('atendente','campanha','create', false, 'Criar e disparar campanha'),
('operador','campanha','create', false, 'Criar e disparar campanha'),
('dono','automacao','update', true, 'Ligar/desligar automação'),
('atendente','automacao','update', false, 'Ligar/desligar automação'),
('operador','automacao','update', true, 'Ligar/desligar automação'),
('dono','canal','update', false, 'Configurar canal e integração'),
('atendente','canal','update', false, 'Configurar canal e integração'),
('operador','canal','update', true, 'Configurar canal e integração'),
('dono','ia_config','update', false, 'Editar prompt e persona'),
('atendente','ia_config','update', false, 'Editar prompt e persona'),
('operador','ia_config','update', true, 'Editar prompt e persona'),
('dono','contato','read', true, 'Ver base de contatos'),
('atendente','contato','read', true, 'Ver base de contatos'),
('operador','contato','read', true, 'Ver base de contatos'),
('dono','contato','export', true, 'Exportar dados'),
('atendente','contato','export', false, 'Exportar dados'),
('operador','contato','export', true, 'Exportar dados');

create or replace function private.has_permission(p_tenant_id uuid, p_recurso text, p_acao text)
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

revoke all on function private.has_permission(uuid, text, text) from public;
grant execute on function private.has_permission(uuid, text, text) to authenticated;

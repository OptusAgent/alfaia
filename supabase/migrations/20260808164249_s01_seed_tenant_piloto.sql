-- Story 1.1 (PRD S-01), Task 6: tenant piloto.
-- Dado fornecido pelo usuario nesta sessao (placeholder ate o primeiro
-- cliente real fechar) — nao inventado.
--
-- NOTA: o segundo passo do Task 6 (criar o primeiro tenant_membros, papel
-- 'dono', para valmirmoreirajunior@gmail.com) NAO foi feito aqui de proposito.
-- auth.users ainda esta vazia — a conta real de autenticacao so passa a
-- existir quando a Story 1.2 (Auth, tenancy e RBAC) implementar o fluxo de
-- signup/convite do Supabase Auth. Criar a linha via INSERT bruto em
-- auth.users (como foi feito nos testes descartaveis de RLS desta story)
-- geraria uma conta sem senha valida — inutilizavel para login real.
-- Ver docs/stories/1.2.story.md para o vinculo.

insert into tenants (nome, slug, cidade, uf, ativo)
values ('valmir', 'loja-teste', 'Fortaleza', 'CE', true);
-- id gerado: 1c217b14-0f39-41d1-84b9-df3cd3443652

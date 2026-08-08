-- Story 1.2 (PRD S-02): has_permission() precisa ser chamavel diretamente
-- pelos guards de rota do Portal (Task 3, AC 2), nao so de dentro de
-- policies de RLS definidas em tempo de DDL. Para isso, 'authenticated'
-- precisa de USAGE no schema private, alem do EXECUTE ja concedido na
-- function. Faltou na migration anterior -- descoberto ao tentar chamar
-- private.has_permission(...) simulando uma sessao autenticada real.
grant usage on schema private to authenticated;

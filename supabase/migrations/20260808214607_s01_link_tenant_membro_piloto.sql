-- Story 1.1/1.2, Task 6 (parte final): usuario real criado pelo usuario via
-- Dashboard do Supabase (valmir@testealfaia.com, nao o gmail originalmente
-- mencionado -- escolha dele). Vincula ao tenant piloto como dono.
insert into tenant_membros (tenant_id, user_id, papel)
values ('1c217b14-0f39-41d1-84b9-df3cd3443652', '2b327e7c-0ccf-474d-90d0-0d25420449bb', 'dono');

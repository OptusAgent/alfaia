-- Seed do horário de funcionamento pedido pelo usuário (2026-08-21) para o tenant piloto:
-- segunda a sexta 09:00-12:00 e 14:00-19:00 (2 turnos), sábado 09:00-14:00, domingo fechado
-- (sem linha = fechado). Aplica a todos os tenants já cadastrados — ajuste por tenant fica
-- disponível assim que a story do CRUD (modal em Configurações) existir.

insert into horarios_funcionamento (tenant_id, dia_semana, hora_abertura, hora_fechamento)
select t.id, dia.dia_semana, dia.hora_abertura, dia.hora_fechamento
from tenants t
cross join (
  values
    -- segunda(1) a sexta(5): turno manhã e turno tarde
    (1, '09:00'::time, '12:00'::time),
    (1, '14:00'::time, '19:00'::time),
    (2, '09:00'::time, '12:00'::time),
    (2, '14:00'::time, '19:00'::time),
    (3, '09:00'::time, '12:00'::time),
    (3, '14:00'::time, '19:00'::time),
    (4, '09:00'::time, '12:00'::time),
    (4, '14:00'::time, '19:00'::time),
    (5, '09:00'::time, '12:00'::time),
    (5, '14:00'::time, '19:00'::time),
    -- sábado(6): turno único
    (6, '09:00'::time, '14:00'::time)
) as dia(dia_semana, hora_abertura, hora_fechamento)
where not exists (
  select 1 from horarios_funcionamento hf
  where hf.tenant_id = t.id and hf.dia_semana = dia.dia_semana and hf.hora_abertura = dia.hora_abertura
);

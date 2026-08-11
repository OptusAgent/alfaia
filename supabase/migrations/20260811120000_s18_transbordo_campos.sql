-- Migration Story 4.5: Adiciona campos de controle de expiração e operador de pausa em conversas (PRD §17.5)

alter table conversas add column if not exists pausada_ate timestamptz;
alter table conversas add column if not exists pausada_por text;

create index if not exists conversas_expiracao_pausa on conversas(pausada_ate)
  where estado in ('humano', 'transbordo') and pausada_ate is not null;

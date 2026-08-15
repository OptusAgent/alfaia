-- Migration Story 6.2: Índice para ordenação rápida da timeline de eventos do lead (PRD §17.4, AC 3)

create index if not exists lead_eventos_lead on lead_eventos(lead_id, criado_em desc);

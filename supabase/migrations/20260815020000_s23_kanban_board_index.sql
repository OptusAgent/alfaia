-- Migration Story 6.1: Índice de alta performance para renderização rápida do Quadro Kanban (PRD §17.4, AC 3, NFR8)

create index if not exists leads_board on leads(tenant_id, status, atualizado_em desc);

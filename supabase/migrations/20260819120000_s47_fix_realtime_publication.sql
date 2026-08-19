-- Fix: a migration 20260811110000_s17_realtime_conversas.sql nunca foi aplicada no projeto
-- remoto (alfa-ia). Resultado: publicacao 'supabase_realtime' ficou sem nenhuma tabela,
-- entao o Portal so via mensagens novas apos hard refresh (Ctrl+Shift+R), nunca em tempo
-- real via WebSocket. Reaplica de forma idempotente (PRD §17.12, NFR9).

begin;
  do $$
  begin
    if not exists (select 1 from pg_publication where pubname = 'supabase_realtime') then
      create publication supabase_realtime;
    end if;
  end $$;

  do $$
  begin
    if not exists (
      select 1 from pg_publication_tables
      where pubname = 'supabase_realtime' and tablename = 'conversas'
    ) then
      alter publication supabase_realtime add table conversas;
    end if;

    if not exists (
      select 1 from pg_publication_tables
      where pubname = 'supabase_realtime' and tablename = 'mensagens'
    ) then
      alter publication supabase_realtime add table mensagens;
    end if;

    if not exists (
      select 1 from pg_publication_tables
      where pubname = 'supabase_realtime' and tablename = 'leads'
    ) then
      alter publication supabase_realtime add table leads;
    end if;

    if not exists (
      select 1 from pg_publication_tables
      where pubname = 'supabase_realtime' and tablename = 'lead_eventos'
    ) then
      alter publication supabase_realtime add table lead_eventos;
    end if;
  end $$;
commit;

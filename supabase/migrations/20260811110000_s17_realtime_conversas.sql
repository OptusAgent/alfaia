-- Migration Story 4.4: Habilitação do Supabase Realtime para conversas, mensagens, leads e lead_eventos (PRD §17.12)

-- Habilita publicação em tempo real para sincronização com latência ≤ 2s no Portal (NFR9, AC 3)
begin;
  -- Garante que a publicação 'supabase_realtime' exista
  do $$
  begin
    if not exists (select 1 from pg_publication where pubname = 'supabase_realtime') then
      create publication supabase_realtime;
    end if;
  end $$;

  -- Adiciona as 4 tabelas especificadas em §17.12
  alter publication supabase_realtime add table conversas;
  alter publication supabase_realtime add table mensagens;
  alter publication supabase_realtime add table leads;
  alter publication supabase_realtime add table lead_eventos;
commit;

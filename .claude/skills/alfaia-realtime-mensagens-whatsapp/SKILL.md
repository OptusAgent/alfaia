---
name: alfaia-realtime-mensagens-whatsapp
description: Referência técnica sobre a funcionalidade de mensagens em tempo real do WhatsApp na tela de Atendimento do Portal ALFAIA (Supabase Realtime + parsing de timestamp do webhook UAZAPI). Esta skill deve ser usada ao investigar por que mensagens não aparecem ao vivo no Portal (só depois de reload), ao mexer no adapter UAZAPI, no parser de webhook, na tabela `mensagens`/`conversas`, ou ao adicionar novo canal/provider de mensageria que precise do mesmo pipeline realtime.
---

# Mensagens em Tempo Real no Portal (WhatsApp)

## O que é essa funcionalidade

A tela de Atendimento (`portal/app/(dashboard)/conversas/page.tsx`) mostra as
conversas de WhatsApp do tenant e precisa refletir mensagens novas — tanto do
lead quanto da IA — sem que o usuário precise dar reload na página (NFR9 do
PRD: latência de sincronização ≤ 2s).

O fluxo completo é:

1. UAZAPI (WhatsApp não-oficial) envia um webhook para o worker (FastAPI) a
   cada mensagem recebida.
2. `worker/app/routers/webhooks.py` normaliza o payload via
   `worker/app/adapters/uazapi.py` (`normalizar_webhook`), grava a mensagem do
   lead na tabela `mensagens` (`remetente='lead'`), chama a IA
   (`ai_engine_service.processar_atendimento`), envia a resposta pelo UAZAPI e
   grava a resposta da IA na mesma tabela (`remetente='ia'`).
3. O Portal (client component) assina um canal Supabase Realtime
   (`supabase.channel(...).on("postgres_changes", ...)`) nas tabelas
   `mensagens` e `conversas` filtrado por `tenant_id`, e re-busca a conversa
   inteira a cada evento.
4. Para o evento chegar ao navegador, a tabela precisa estar na *publication*
   `supabase_realtime` do Postgres **e** a RLS da tabela precisa permitir
   `SELECT` para o usuário autenticado (Realtime reavalia RLS por conexão).

Esse pipeline pode quebrar em qualquer um dos 4 pontos acima sem gerar erro
visível — a query REST normal continua funcionando, só o "ao vivo" para de
funcionar. É por isso que o sintoma clássico é "só atualiza com
Ctrl+Shift+R".

## O que foi encontrado quebrado (19/08/2026)

Dois bugs completamente independentes, cada um mascarando o outro:

### Bug 1 — publication `supabase_realtime` vazia no projeto remoto

A migration `supabase/migrations/20260811110000_s17_realtime_conversas.sql`
(Story 4.4) faz `alter publication supabase_realtime add table
conversas/mensagens/leads/lead_eventos` — mas essa migration nunca foi de
fato aplicada no projeto Supabase de produção (`alfa-ia`,
`irewoqkwywsapiiytdau`). A tabela `supabase_migrations.schema_migrations` no
projeto remoto tinha só 14 registros contra 30 arquivos locais.

Diagnóstico (rodar sempre que "realtime parou de funcionar" for reportado):

```sql
select p.pubname, c.relname
from pg_publication p
join pg_publication_tables pt on pt.pubname = p.pubname
join pg_class c on c.relname = pt.tablename
where p.pubname = 'supabase_realtime'
order by c.relname;
-- se a tabela relevante não aparecer aqui, o Postgres nunca vai
-- emitir WAL event pra ela e o canal Realtime nunca vai disparar.
```

RLS não era o problema neste caso — as policies `*_tenant` (`for all ...
using (tenant_id in (select tenant_id from tenant_membros where user_id =
auth.uid()))`) já existiam corretas em `mensagens`, `conversas`, `leads` e
`lead_eventos`.

### Bug 2 — timestamp do lead sempre caindo num fallback fixo de 07/08/2025

Mesmo depois de corrigir a publication, a mensagem da IA aparecia quase
instantânea, mas a mensagem do **lead** nunca aparecia — não por atraso, e
sim porque ela sempre nascia com `enviado_em = '2025-08-07 12:33:20+00'`
(uma data fixa hardcoded, sempre a mesma, independente de quando a mensagem
foi realmente recebida).

Causa: em `worker/app/adapters/uazapi.py`, a extração do timestamp só olhava
`data` (payload top-level) e `data_node` (`data.data`/`data.payload`):

```python
timestamp = first_value(
    get_any(data, "timestamp", "Timestamp", "messageTimestamp", "MessageTimestamp"),
    get_any(data_node, "timestamp", "Timestamp", "messageTimestamp", "MessageTimestamp"),
    1754570000,  # fallback hardcoded = 2025-08-07 12:33:20 UTC
)
```

Só que no payload real da UAZAPI (confirmado lendo `webhook_capturas.corpo`
em produção), o campo vem em `message.messageTimestamp` — dentro de
`message_node`, que **não estava na lista de lugares checados**. Resultado:
o campo nunca era encontrado e o parser caía sempre no fallback fixo.

Consequência no front-end: `conversas/page.tsx` ordena as mensagens de cada
conversa por `enviado_em`. Com a mensagem do lead presa em ago/2025, ela era
ordenada lá no topo da lista (fora da área visível de quem rola até o fim da
conversa) e nunca era escolhida como `ultima_mensagem` (preview da lista de
conversas), que usa `msgs.at(-1)` após o sort.

Um segundo detalhe do mesmo bug: `messageTimestamp` da UAZAPI/Baileys vem em
**milissegundos** (13 dígitos, ex: `1787142609000`), não em segundos. Se
fosse lido sem normalizar, `datetime.fromtimestamp(1787142609000, utc)`
estouraria (ano ~58631) e cairia em outro fallback por exceção — outro
sintoma possível do mesmo tipo de bug.

## O que foi feito para corrigir

Commit: `03028ff` — `fix(worker): corrigir timestamp de mensagens do lead e
ativar realtime no portal` (em `main`).

1. **`supabase/migrations/20260819120000_s47_fix_realtime_publication.sql`**
   — reaplica `alter publication supabase_realtime add table` de forma
   idempotente (`if not exists` contra `pg_publication_tables`) para
   `conversas`, `mensagens`, `leads`, `lead_eventos`. Aplicado no projeto
   remoto via MCP Supabase (`apply_migration`) e verificado com o SQL de
   diagnóstico acima.

2. **`worker/app/adapters/uazapi.py`** — a extração de timestamp passou a:
   - checar também `message_node` na cadeia de `first_value(...)`;
   - normalizar milissegundos→segundos (`if timestamp_epoch >
     10_000_000_000: timestamp_epoch //= 1000`);
   - trocar o fallback fixo (`1754570000`) por um fallback dinâmico
     (`int(datetime.now(timezone.utc).timestamp())`), do mesmo jeito que
     `datetime_from_timestamp()` em `webhooks.py` já fazia para a mensagem
     da IA.

3. **`worker/tests/test_uazapi_adapter.py`** — teste de regressão
   (`test_uazapi_normalizar_webhook_extrai_timestamp_ms_do_message_node`)
   reproduzindo o payload real capturado em produção, garantindo que
   `messageTimestamp` dentro de `message` é lido e normalizado
   corretamente.

4. **`supabase/migrations/20260819120100_s48_backfill_enviado_em_lead_timestamp_bug.sql`**
   — backfill de dados: as 4 mensagens de lead já gravadas em produção com
   `enviado_em = '2025-08-07 12:33:20+00'` tiveram esse campo corrigido para
   `criado_em` (o momento real em que a mensagem chegou), restaurando a
   ordem cronológica das conversas já existentes.

5. Validação: suíte completa do worker (`pytest`, 136 testes) passando;
   confirmação manual pelo usuário mandando mensagem real no WhatsApp com a
   tela do Atendimento aberta, sem reload.

## Checklist para o próximo bug parecido

Ao investigar "mensagem não chega em tempo real" ou "aparece fora de ordem /
some da lista" no Atendimento:

1. Rodar o SQL de diagnóstico da publication (Bug 1) no projeto Supabase
   relevante — nunca assumir que uma migration local foi de fato aplicada no
   remoto, sempre conferir `pg_publication_tables` e
   `supabase_migrations.schema_migrations` diretamente.
2. Se a publication estiver ok, olhar `mensagens.enviado_em` das últimas
   linhas — comparar com `criado_em`. Se houver um valor fixo repetido em
   várias linhas, é sinal de fallback hardcoded no parser do adapter, não de
   atraso de rede.
3. Para qualquer campo extraído de webhook (telefone, texto, timestamp,
   wa_message_id), confirmar que a busca cobre `data`, `data_node` **e**
   `message_node`/`key_node` — o payload real da UAZAPI é aninhado e varia
   de formato (camelCase, PascalCase, `data.message.*`, `message.*` direto).
   Usar `webhook_capturas.corpo` (payload bruto salvo por
   `webhook_service.capturar_bruto`) para confirmar o formato real antes de
   consertar às cegas.
4. Nunca usar constantes de data/hora "prontas" como fallback silencioso —
   usar `datetime.now(timezone.utc)` (padrão já usado em
   `datetime_from_timestamp()` em `webhooks.py`).

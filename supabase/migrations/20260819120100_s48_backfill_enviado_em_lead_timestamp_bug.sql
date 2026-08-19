-- Backfill: corrige mensagens de lead com enviado_em preso no fallback fixo do
-- bug em worker/app/adapters/uazapi.py (timestamp da UAZAPI/Baileys vem em
-- message.messageTimestamp, em milissegundos, mas o parser so olhava data/
-- data_node e nunca message_node — toda mensagem de lead nascia com
-- enviado_em = 2025-08-07 12:33:20+00, ficando fora de ordem na conversa e
-- nunca aparecendo como "ultima mensagem" no Portal).

update mensagens
set enviado_em = criado_em
where enviado_em = '2025-08-07 12:33:20+00'
  and remetente = 'lead';

# Referência técnica — AuctaFlux Reseller API (canal Meta oficial)

> Levantado em 08/08/2026 para desbloquear a story [2.4 — Adapter Meta/AuctaFlux](../stories/2.4.story.md) (PRD S-06). **A documentação oficial em `https://flux.aucta.tech/reseller/docs` é renderizada em JavaScript (SPA) e não pôde ser lida por fetch automatizado** — a tentativa retornou apenas o esqueleto da página, sem conteúdo técnico. Este documento reúne o que foi confirmado a partir de duas fontes reais lidas nesta sessão e marca explicitamente o que não pôde ser confirmado.

## Fontes usadas

1. `/home/valmir/Documentos/ALFAIA/MCP_CONECTION_AUCTA.md` — página de onboarding do MCP server oficial da AuctaFlux.
2. `/home/valmir/Documentos/ALFAIA/AUCTA.png` — screenshot da página npm do pacote `@auctaflux/reseller-mcp` (README completo, incluindo tabela de rotas, erros e limites).
3. `PRD-ALFAIA-v2.md` §14 (M7 — Canal WhatsApp dual), que já documentava o comparativo UAZAPI vs. Meta/AuctaFlux antes desta pesquisa.

**Nenhuma informação abaixo foi inventada.** Onde a fonte não confirma um detalhe, isso está listado em "Gaps".

## Autenticação

- Chave "reseller": formato `aflx_rsl_...`.
- Uma única chave controla **todas as instâncias** (workspaces) da conta.
- Env var usada pelo MCP oficial: `AUCTAFLUX_RESELLER_API_KEY`.
- Base URL configurável via `AUCTAFLUX_BASE_URL` (exemplo documentado: `https://api-flux.aucta.tech`) — permite apontar para self-hosted/staging.
- Já prevista no PRD (§24, variáveis de ambiente): `AUCTAFLUX_BASE_URL`, `AUCTAFLUX_RESELLER_API_KEY`.

## Modelo de recursos

Unidade central: **workspace** = uma instância/número de WhatsApp conectado.

## Rotas REST (mapeadas 1:1 a partir das 22 ferramentas do MCP oficial — o MCP é um proxy fino sobre a REST API, não uma abstração própria)

| Ferramenta MCP | Método | Rota | Uso no ALFAIA |
|---|---|---|---|
| list_instances | GET | `/workspaces` | Listar canais Meta do tenant |
| get_instance | GET | `/workspaces/{id}` | Status do canal |
| create_instance | POST | `/workspaces` | Onboarding (story 8.3) |
| update_instance | PATCH | `/workspaces/{id}` | Atualizar nome/webhook |
| archive_instance | DELETE | `/workspaces/{id}` | Desativar canal |
| get_connection_status | GET | `/workspaces/{id}/connection` | Health check do canal |
| create_connect_link | POST | `/workspaces/{id}/connect-link` | Onboarding — link para o cliente conectar o número |
| register_connection | POST | `/workspaces/{id}/connection/register` | Onboarding — envio do PIN 2FA |
| disconnect_connection | DELETE | `/workspaces/{id}/connection` | Desconectar sem arquivar |
| rotate_forward_secret | POST | `/workspaces/{id}/rotate-secret` | Rotacionar o segredo HMAC do webhook |
| send_text_message | POST | `/workspaces/{id}/messages` | `enviar_texto` (story 2.4) |
| send_template_message | POST | `/workspaces/{id}/messages/template` | `enviar_template` |
| send_media_message | POST | `/workspaces/{id}/messages/media` | `enviar_midia` |
| send_interactive_message | POST | `/workspaces/{id}/messages/interactive` | Fora de escopo do PRD v1 (sem menu/botões, Princípio P1) — não usar |
| mark_message_as_read | POST | `/workspaces/{id}/messages/{wamid}/read` | `marcar_lido` |
| delete_message | DELETE | `/workspaces/{id}/messages/{wamid}` | Não usado no PRD |
| list_templates | GET | `/workspaces/{id}/templates` | Listar templates aprovados (para K2, campanhas) |
| create_template | POST | `/workspaces/{id}/templates` | Submeter template à Meta |
| delete_template | DELETE | `/workspaces/{id}/templates?name=...` | — |
| get_business_profile | GET | `/workspaces/{id}/profile` | — |
| update_business_profile | PATCH | `/workspaces/{id}/profile` | — |
| get_usage | GET | `/usage` | Monitoramento de uso (Épico 9) |

`sync_contacts` e `sync_history` também existem como ferramentas MCP, mas suas rotas exatas não apareceram na tabela do README (cortada no screenshot) — fora de escopo do PRD v1 de qualquer forma (§5.2: sem importação de histórico de contatos como funcionalidade do produto).

## Formato de erro (confirmado)

```json
{"error": {"code": "...", "message": "..."}}
```

Mapeado pelo MCP para `isError: true`. Códigos conhecidos:

| Code | Significado |
|---|---|
| `RATE_LIMIT_EXCEEDED` | 1000 req/min atingido — aguardar 60s |
| `WORKSPACE_NOT_FOUND` | `workspace_id` inválido |
| `CONNECTION_NOT_FOUND` | Workspace sem conexão WhatsApp |
| `PIN_REQUIRED` | 2FA necessário — usar `register_connection` |
| `PIN_MISMATCH` | PIN incorreto |
| `WORKSPACE_ARCHIVED` | Workspace arquivado |
| `META_API_ERROR` | Meta rejeitou a requisição |

## Fluxo de onboarding de número (inferido da sequência lógica das ferramentas — não há um "quick start" de onboarding completo na fonte)

1. `create_instance` — cria o workspace.
2. `create_connect_link` — gera link de onboarding para o cliente final escanear/conectar.
3. Cliente conecta o número no WhatsApp Business App.
4. `register_connection` — envia o PIN 2FA recebido.
5. `get_connection_status` — confirma que a conexão está ativa.

## Fora de escopo da V1 do pacote MCP (declarado na própria fonte)

- Upload de mídia via MCP (`POST /workspaces/{id}/media`) — usar o Console da Reseller e passar `media_id` para `send_media_message`.
- CRUD de API Keys — só pelo Console.
- MCP hospedado via HTTP (V1 é stdio, roda na máquina do cliente) — mencionado como possibilidade futura.

## Gaps — não confirmados, não inventar

Estes quatro pontos bloqueiam o fechamento (não o início) da story 2.4:

| # | Gap | Por que importa |
|---|---|---|
| G1 | Nome exato do header HMAC e algoritmo de assinatura do webhook (`forward_to_url`) | Sem isso, `normalizar_webhook`/validação HMAC da story 2.4 (AC 2, AC 14.3) não pode ser implementada contra o formato real — apenas contra uma suposição |
| G2 | Formato literal do payload JSON que a AuctaFlux envia para `forward_to_url` | Mesma story — o parser de webhook precisa do schema real |
| G3 | Onde `forward_to_url` é configurado (corpo de `create_instance`/`update_instance`? endpoint dedicado?) | Bloqueia o passo de onboarding automatizado (story 8.3) para canal Meta |
| G4 | Schemas de request/response completos por rota (bodies, campos obrigatórios) | A tabela acima só confirma método+rota, não o contrato de dados completo |

**Ação recomendada:** quando as credenciais da Aucta chegarem (o usuário confirmou que ainda não as tem), o primeiro passo prático é rodar o smoke test descrito no próprio README (`ACTAFLUX_RESELLER_API_KEY=aflx_rsl_... npx @modelcontextprotocol/inspector`) e capturar um webhook real de teste — isso resolve G1–G3 em minutos, sem depender de acesso à doc site.

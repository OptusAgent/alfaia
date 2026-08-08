# ALFAIA — Coding Standards

> Aplica-se a todo código de produção em `/portal` (Next.js) e `/worker` (FastAPI). Não se aplica a `frontend/` (protótipo congelado, ver `tech-stack.md` §2).

## 1. Princípios do produto que restringem o código (PRD §1.2, §3, §19.2)

Estes não são "boas práticas" genéricas — são regras invioláveis do produto e devem ser refletidas em código, testes e prompts:

- **Nada de dado inventado (P3):** qualquer valor de disponibilidade, horário ou preço no fluxo de IA vem de uma chamada de ferramenta real na conversa corrente. Se a chamada falhar, o caminho de código correto é abrir transbordo — nunca preencher com suposição, default silencioso ou cache stale além do TTL de 60s (A4).
- **Fronteira F1–F6:** nenhuma função do worker pode escrever em contrato, financeiro, estoque ou nota fiscal, nem disparar os 7 templates transacionais já existentes na WebLocação. Se uma story pedir isso, é uma lacuna do PRD — pare e escale ao @po, não implemente.
- **Humano tem prioridade absoluta (P4):** qualquer código do motor de IA deve checar estado de transbordo/assunção humana antes de gerar ou enviar resposta.
- **Autoria de movimentação de status (A9):** toda mudança de status de lead grava `autor` (`ia` | `humano`). Não existe update de status sem esse campo.
- **IA nunca marca `ganho`:** regra de negócio codificada como validação explícita na camada que aplica mudança de status, não como convenção de prompt apenas.

## 2. Backend — FastAPI (worker)

- Python tipado (type hints obrigatórios em toda função pública); `mypy`/checagem equivalente antes de marcar story como pronta.
- Toda chamada à API WebLocação passa pela camada anticorrupção (I7) — nenhum campo do ERP é usado fora dela sem tradução para o modelo interno.
- Timeout de 8s e retry com backoff (máx. 2, apenas em 5xx) são implementados uma vez na camada de integração, não replicados por chamador (I2, I4).
- Toda chamada à WebLocação é logada em `wl_chamadas` com latência e status (I3) — não é opcional, não é best-effort.
- Debounce usa `FOR UPDATE SKIP LOCKED` (A5) — não implementar debounce com lock em memória do processo, o worker roda multi-processo/multi-instância.
- Toda tool exposta ao motor de IA tem schema validado; resposta inválida do LLM é rejeitada com reprompt único antes de transbordo (§21.2) — não aceitar tool call malformada silenciosamente.
- Escrita de agenda é idempotente por `(tenant_id, lead_id, data, hora)` (I6) — usar upsert/constraint, não checagem de aplicação apenas.
- Jobs agendados (§18.3) implementados de forma portável (loop interno / cron), sem dependência de scheduler proprietário de nuvem — ver `tech-stack.md` §3.
- Logs estruturados em JSON com os campos de §21.1 (`tenant_id`, `canal_id`, `conversa_id`, `lead_id`, `wa_message_id`, `etapa`, `latencia_ms`, `resultado`, `erro`) — sem exceção, é o único meio de observabilidade do produto.

## 3. Frontend — Next.js 15 (portal)

- App Router; route handlers para toda a API interna listada em §18.2 do PRD.
- Toda rota de API valida a permissão do papel (`dono`/`atendente`/`operador`) descrita em §4.2 antes de executar a ação — usar o helper `has_permission(recurso, acao)` também no guard de rota, não só na policy de RLS.
- Nenhum dado pessoal em URL ou query string (S4) — inclusive em rotas internas de exportação.
- Client components não fazem chamada direta a Supabase com a service key; apenas com a anon key sob RLS, ou via route handler server-side quando a operação exigir privilégio elevado.
- Acessibilidade: WCAG 2.1 AA nos fluxos principais (NFR12); responsivo a partir de 360px (NFR13) — validar Kanban, chat e agenda nessas condições antes de story fechar.

## 4. Banco de dados / Supabase

- RLS habilitada em toda tabela com `tenant_id`; proibida qualquer policy `using (true)` (S1) — isso é gate de PR, não sugestão.
- `tenant_id` presente em toda tabela de domínio (A1) desde a migration inicial — não adicionar depois.
- Credenciais de canal e chave da WebLocação apenas server-side, em coluna criptografada ou secret store — nunca em código, nunca expostas ao client (I1, S2).
- Toda migration é aplicada e confirmada no Supabase **antes** do push (§24, sequência de deploy) — nunca depois.
- Histórico de interesse do lead é append-only em tabela própria (A10) — nunca overwrite do registro anterior.

## 5. Multi-tenant e segurança (LGPD)

- Nenhuma query cross-tenant, nem em job agendado, nem em endpoint administrativo, sem passar pela mesma checagem de `tenant_id` que o resto do sistema.
- Exclusão de contato é cascata real (contato, leads, mensagens, alvos de campanha) — S8.
- Exportação de dados restrita a `dono` e `operador` (S12) e logada (S5).
- Retenção de mensagens 24 meses; após isso, anonimização mantendo métricas (S9) — implementar como job, não como processo manual.

## 6. Testes (PRD §23)

Cobertura mínima por camada, sem exceção:

| Camada | Tipo | O que cobrir |
|---|---|---|
| Adapters de canal | Unitário | Normalização de telefone, HMAC, idempotência, headers — 100% dos caminhos |
| `identificar_lead` | Integração (banco real) | Os 7 cenários da matriz §9.4 |
| Motor de IA | Contrato | Toda tool com schema validado; recusa a inventar dado |
| Engine de follow-up | Unitário | Janela, tentativas, zeragem |
| Engine de campanha | Unitário | K1–K8 |
| RLS | Integração | Tentativa de acesso cross-tenant deve falhar |
| Portal | E2E | Kanban drag-drop, assumir/devolver, disparo de follow-up |

Os 12 casos de teste obrigatórios (T1–T12, PRD §23.2) cobrem identificação/retomada/reengajamento de lead e são bloqueantes para as stories de E3.

## 7. Convenções gerais

- Imports absolutos (Artigo VI da Constitution AIOX) — evitar `../../..` em ambos os serviços.
- Commits: conventional commits (`feat:`, `fix:`, `docs:`, `chore:`) referenciando a story: `feat: implementa identificar_lead [Story S-09]`.
- Nenhum código de produção assume qual VPS hospedará a produção final (EasyPanel/Hostinger vs Dockplot/Contabo) — ver `tech-stack.md` §3.
- Toda entrega declara explicitamente se exige migration no Supabase e/ou redeploy, e em qual serviço (§24) — isso vai no PR, não só na story.
- **Idioma:** toda comunicação, documentação, commit, PR e resposta de agente é em PT-BR, sem exceção — ver `.claude/rules/language-policy.md`. Identificadores de código e nomes de tecnologia permanecem no idioma técnico original.

## 8. Definition of Done (PRD §27.2) — checklist mecânico

- [ ] Todos os ACs verificados pelo @qa
- [ ] Testes da §23 aplicáveis passando
- [ ] Typecheck e lint zerados
- [ ] Migration aplicada e confirmada antes do push
- [ ] RLS verificada quando a story cria tabela
- [ ] File List e Change Log atualizados
- [ ] PR aberto contra `main`, revisado e aprovado
- [ ] Declarado explicitamente se exige ajuste no Supabase e/ou redeploy
- [ ] Nenhuma regressão nos fluxos existentes

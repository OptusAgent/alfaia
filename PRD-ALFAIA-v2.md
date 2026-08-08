# PRD — ALFAIA
### Plataforma de atendimento e CRM conversacional para locadoras de trajes

| | |
|---|---|
| **Versão** | 2.1 |
| **Data** | 07/08/2026 (emenda §24 em 08/08/2026 — @po) |
| **Autor** | Valmir Moreira Junior — Optus Agent |
| **Metodologia** | AIOX (@sm River · @po Pax · @dev Dex · @qa Quinn · @devops Gage) |
| **Stack** | Next.js 15 (portal) · FastAPI (worker) · Supabase (Postgres + Auth + Realtime + Storage) |
| **Status** | Draft para validação interna |

> **Nota de método.** Este documento é a fonte única de verdade do produto. Nenhuma decisão de produto ou de arquitetura pode ser tomada dentro de uma story sem estar aqui. Se o @dev encontrar uma lacuna durante a implementação, a story é interrompida (HALT) e o PRD é emendado pelo @po antes de prosseguir. Toda seção com ACs numerados é rastreável na matriz da seção 26.

---

## Índice

| § | Seção |
|---|---|
| 1 | Contexto e fronteira |
| 2 | Problema |
| 3 | Visão e princípios |
| 4 | Personas e RBAC |
| 5 | Escopo |
| 6 | Arquitetura |
| 7 | Integração WebLocação |
| 8 | M1 — Atendimento IA |
| 9 | **M2 — Identificação, retomada e reengajamento** |
| 10 | M3 — CRM Kanban |
| 11 | M4 — Agenda |
| 12 | M5 — Consulta de produtos |
| 13 | M6 — Transbordo |
| 14 | M7 — Canal WhatsApp dual |
| 15 | M8 — Base de contatos e campanhas |
| 16 | M9 — Automações |
| 17 | Modelo de dados |
| 18 | API interna |
| 19 | Prompt de sistema |
| 20 | Requisitos não funcionais |
| 21 | Observabilidade e erros |
| 22 | Segurança e LGPD |
| 23 | Testes |
| 24 | Ambientes e deploy |
| 25 | Roadmap, épicos e stories |
| 26 | Matriz de rastreabilidade |
| 27 | Definition of Ready / Done |
| 28 | Glossário |
| 29 | Questões abertas |

---

## 1. Contexto e fronteira

A WebLocação é um ERP SaaS para locadoras de roupas, vestidos, trajes e acessórios, com mais de 10 anos de mercado. Já executa disparos transacionais via WhatsApp Business API própria (7 templates: novo pedido, lembrete de prova, lembrete de atendimento, assinatura digital, lembrete de retirada, lembrete de devolução, produto consignado).

Na demonstração de 07/08/2026 a proposta original foi interpretada como sobreposição ao produto deles. O escopo foi renegociado e este PRD reflete exclusivamente o escopo acordado.

### 1.1 Modelo de relacionamento

- **ALFAIA é produto da Optus Agent** — plataforma própria, independente e apartada da WebLocação do início ao fim.
- A WebLocação atua como **canal de indicação**, não como sócia da plataforma.
- A WebLocação disponibiliza endpoints de integração conforme seção 7.
- O cliente final (a locadora) é cliente direto da Optus Agent.

### 1.2 Fronteira — o que o ALFAIA nunca faz

**Seção normativa.** Qualquer story que viole um item desta tabela é rejeitada no refinamento pelo @po, sem exceção e sem negociação em tempo de execução.

| # | O ALFAIA não | Motivo |
|---|---|---|
| F1 | Dispara os templates transacionais da WebLocação | É produto deles, já em operação |
| F2 | Escreve contrato, pedido, financeiro, parcela, nota fiscal ou estoque | Sistema de registro é o ERP |
| F3 | Mantém acervo próprio, cadastro de peças ou catálogo espelhado | Consulta em tempo real, sem persistir catálogo |
| F4 | Altera agendamento fora do fluxo da automação | Alteração manual é feita no portal da WebLocação |
| F5 | Gerencia consignantes, repasses, eventos ou convidados | Fora do escopo acordado |
| F6 | Substitui qualquer tela do ERP | ALFAIA é complemento, não concorrente |

---

## 2. Problema

A locadora recebe leads pelo WhatsApp fora do horário comercial e em volume desorganizado. Hoje:

1. Ninguém responde à noite, no fim de semana ou durante atendimento presencial — o lead esfria ou vai para o concorrente.
2. Consultar disponibilidade exige abrir o ERP, filtrar, voltar ao WhatsApp e digitar.
3. O lead que pediu orçamento e sumiu não é perseguido. Sem registro, sem follow-up, sem visibilidade da perda.
4. Quem volta a falar meses depois é tratado como estranho — a loja não lembra do que ele queria.
5. Não há base de contatos aproveitável para remarketing sazonal.

O gargalo não é o ERP. É a camada de conversa e relacionamento ao redor dele.

---

## 3. Visão e princípios

> Uma plataforma que atende o lead da locadora pelo WhatsApp 24 horas por dia, reconhece quem já falou antes, consulta a disponibilidade real no ERP, agenda a prova, e organiza cada lead num CRM que se move sozinho conforme a conversa evolui.

| # | Princípio | Consequência de projeto |
|---|---|---|
| P1 | **Sem menu numérico** | O lead escreve livremente; nunca "digite 1 para" |
| P2 | **Direto ao ponto** | Respostas curtas, sem preâmbulo, sem repetir o que o lead disse |
| P3 | **Nada de dado inventado** | Disponibilidade, horário e valor vêm sempre da API; falha → transbordo |
| P4 | **O humano tem prioridade absoluta** | Atendente assume e a IA cala; volta só por ação explícita |
| P5 | **Nenhum lead se perde** | Todo contato vira registro; descartado sai do quadro mas fica na base |
| P6 | **Canal é infraestrutura** | Trocar UAZAPI ↔ Meta não muda nenhuma regra de negócio |
| P7 | **O CRM se move sozinho** | A IA move o card conforme o teor da conversa; o humano corrige quando quiser |
| P8 | **Ninguém é estranho duas vezes** | Quem já falou é reconhecido e a conversa retoma de onde parou |

---

## 4. Personas e RBAC

### 4.1 Personas

| Persona | Papel | Uso principal |
|---|---|---|
| **Dona da loja** (Juliana, 41) | Decisora e usuária diária | Kanban, disparo de follow-up, agenda, campanhas |
| **Atendente** (Rafaela, 26) | Operação | Assume conversas, transbordo, acompanha provas |
| **Lead** (Marcela, 29) | Cliente final | Conversa no WhatsApp, nunca vê a plataforma |
| **Operador Optus** (Junior) | Provisionamento e suporte | Cria tenant, conecta canal, configura integração e prompt |

### 4.2 Papéis e permissões

| Recurso | `dono` | `atendente` | `operador` |
|---|---|---|---|
| Ver pipeline e leads | ✅ | ✅ | ✅ |
| Mover card / editar lead | ✅ | ✅ | ✅ |
| Descartar lead | ✅ | ✅ | ✅ |
| Disparar follow-up | ✅ | ✅ | ❌ |
| Assumir / devolver conversa | ✅ | ✅ | ✅ |
| Criar e disparar campanha | ✅ | ❌ | ❌ |
| Ligar/desligar automação | ✅ | ❌ | ✅ |
| Configurar canal e integração | ❌ | ❌ | ✅ |
| Editar prompt e persona | ❌ | ❌ | ✅ |
| Ver base de contatos | ✅ | ✅ | ✅ |
| Exportar dados | ✅ | ❌ | ✅ |

Implementação: tabela `tenant_membros.papel` + helper `has_permission(recurso, acao)` usado nas policies de RLS e nos guards das rotas do portal.

---

## 5. Escopo

### 5.1 IN

| Módulo | Descrição |
|---|---|
| **M1** Atendimento IA | Motor conversacional com tool calling |
| **M2** Identificação e retomada | Reconhecimento do lead, retomada de contexto e movimentação automática de status |
| **M3** CRM Kanban | Pipeline visual, timeline, follow-up, descarte com retenção |
| **M4** Agenda | Visualização por período; leitura da WebLocação |
| **M5** Consulta de produtos | Busca em tempo real, sem catálogo local |
| **M6** Transbordo | Assumir, responder e devolver para a IA |
| **M7** Canal dual | UAZAPI + Meta Cloud API com seletor dinâmico |
| **M8** Base e campanhas | Contatos permanentes, segmentação, disparo em massa |
| **M9** Automações | Rotinas com liga/desliga e log |

### 5.2 OUT (v1)

Acervo próprio; eventos e convidados; consignantes; disparos transacionais; escrita em contrato/financeiro/estoque; app mobile nativo; multi-loja por tenant; BI avançado; atendimento por outros canais (Instagram DM, e-mail, site).

---

## 6. Arquitetura

### 6.1 Componentes

```
   WhatsApp          ┌──────────────────────────────┐
   (lead)  ─────────▶│  Gateway de canal            │
                     │  ├─ Adapter UAZAPI           │
                     │  └─ Adapter Meta (BSP)       │
                     └──────────┬───────────────────┘
                                │ payload normalizado
                     ┌──────────▼───────────────────┐
                     │  Worker FastAPI              │
                     │  ├─ Identificação de lead    │
                     │  ├─ Debounce/buffer          │
                     │  ├─ Motor de IA (tools)      │
                     │  ├─ Engine de CRM/follow-up  │
                     │  └─ Engine de campanhas      │
                     └──────┬──────────────┬────────┘
                            │              │
               ┌────────────▼───┐   ┌──────▼─────────────┐
               │   Supabase     │   │  API WebLocação    │
               │  Postgres/RLS  │   │  produtos + agenda │
               │  Realtime      │   └────────────────────┘
               └────────┬───────┘
                        │ realtime
               ┌────────▼───────┐
               │ Portal Next.js │
               └────────────────┘
```

### 6.2 Decisões de arquitetura

| # | Decisão | Justificativa |
|---|---|---|
| A1 | Multi-tenant desde o dia 1, `tenant_id` em toda tabela, RLS por tenant | Produto nasce para escalar por indicação |
| A2 | Adapter de canal com interface única | P6 |
| A3 | Payload interno normalizado como contrato-alvo dos dois adapters | Padrão validado no Cuca Atende Mais |
| A4 | Sem cache persistente de produtos; cache em memória TTL 60s | F3 |
| A5 | Debounce via Postgres `FOR UPDATE SKIP LOCKED` | Concorrência multi-processo |
| A6 | Motor de IA com tool calling, não máquina de estados rígida | P1 |
| A7 | Follow-up por worker agendado (cron), não trigger de banco | Precisa consultar janela de 24h e canal |
| A8 | **Identificação de lead antes do debounce** | O lead precisa existir mesmo que a IA não responda (P5) |
| A9 | Movimentação de status é gravada com autor (`ia` ou `humano`) | Auditoria e resolução de conflito (§9.7) |
| A10 | Histórico de interesse em tabela própria, não sobrescrito | Permite detectar mudança de interesse (§9.6) |

### 6.3 Contrato interno normalizado

Ambos os adapters produzem exatamente este payload:

```python
{
  "tenant_id":      "uuid",
  "canal_id":       "uuid",
  "provider":       "uazapi" | "meta",
  "telefone":       "5585988124477",   # só dígitos, com DDI
  "push_name":      "Marcela Prado",
  "mensagem":       "tenho um casamento dia 12/09...",
  "midia_url":      None,
  "midia_tipo":     "text",            # text | audio | image | document
  "wa_message_id":  "wamid.HBg...",
  "timestamp":      1754570000,
  "data_atual":     "Sexta-feira, 7 de agosto de 2026, 14:32",
}
```

**Normalização de telefone** (idêntica nos dois adapters): remove tudo que não é dígito; se resultar em 10 ou 11 dígitos sem prefixo `55`, prefixa `55`. Comparação sempre pela forma normalizada.

---

## 7. Integração WebLocação

### 7.1 Acesso concedido

| Recurso | Acesso |
|---|---|
| Produtos e status dos produtos | **Leitura** |
| Agenda — horários e vagas | **Leitura e escrita** |

### 7.2 Contrato esperado

```http
GET  /produtos?data_inicio=&data_fim=&categoria=&tamanho=&cor=&estilo=&q=
     → [{ id, codigo, nome, categoria, tamanho, cor, estilo, valor_locacao, status, foto_url }]

GET  /produtos/{id}
     → { ...detalhe..., disponivel_em: [{inicio, fim}] }

GET  /agenda/slots?tipo=&data_inicio=&data_fim=
     → [{ data, hora, vagas_totais, vagas_livres }]

POST /agenda
     body: { tipo, data, hora, cliente_nome, cliente_telefone, produto_id?, observacao? }
     → { id, status }

GET  /agenda?data_inicio=&data_fim=
     → [{ id, tipo, data, hora, cliente_nome, cliente_telefone, produto, origem }]
```

### 7.3 Regras de integração

| # | Regra |
|---|---|
| I1 | Auth por chave por tenant, em coluna criptografada; nunca no código nem exposta ao client |
| I2 | Timeout 8s; falha nunca derruba a conversa — a IA informa que vai confirmar e abre transbordo |
| I3 | Toda chamada logada em `wl_chamadas` com latência e status |
| I4 | Retry com backoff em 5xx (máx. 2). 4xx sem retry |
| I5 | A resposta da API é a verdade; a IA nunca completa lacuna com suposição |
| I6 | Escrita de agenda idempotente por `(tenant_id, lead_id, data, hora)` |
| I7 | Camada anticorrupção: nenhum campo do ERP vaza para o domínio interno sem tradução |
| I8 | Implementação mock obrigatória com o mesmo contrato, ativável por env `WL_MODO=mock\|real` |

---

## 8. M1 — Atendimento IA

### 8.1 Comportamento

O lead escreve livremente. A IA identifica intenção e aciona ferramentas. Não há menu nem árvore de decisão exposta.

### 8.2 Ferramentas do motor

| Tool | Parâmetros | Efeito |
|---|---|---|
| `buscar_produtos` | evento, estilo, categoria, cor, tamanho, data_inicio, data_fim, q | Leitura WL |
| `consultar_slots` | tipo, data_inicio, data_fim | Leitura WL |
| `agendar` | tipo, data, hora, produto_ref, observacao | Escrita WL |
| `atualizar_lead` | evento_tipo, evento_data, papel, peca_interesse, tamanho, cor, valor_estimado | Escrita local |
| `mover_status` | status_destino, motivo | Escrita local |
| `registrar_interesse` | snapshot do interesse atual | Escrita local |
| `abrir_transbordo` | motivo, criticidade | Escrita local |
| `encerrar` | desfecho (`ganho`\|`descartado`), motivo | Escrita local |

### 8.3 Pipeline de processamento

| # | Etapa | Observação |
|---|---|---|
| 1 | Webhook recebe → responde **200 imediatamente** | Anti-ban (UAZAPI) e anti-reenfileiramento (Meta) |
| 2 | Valida assinatura (HMAC Meta) ou token (UAZAPI) | §14.4 |
| 3 | Idempotência por `wa_message_id` | Descarta duplicata |
| 4 | **Identificação do lead (§9)** | Cria ou recupera contato + lead |
| 5 | Persiste mensagem em `mensagens` | Sempre, mesmo se a IA não for responder |
| 6 | Se conversa pausada por humano → **para aqui** | Notifica portal via realtime |
| 7 | Debounce 8s agrupando mensagens do mesmo contato | `FOR UPDATE SKIP LOCKED` |
| 8 | Áudio → transcrição → texto | Whisper |
| 9 | Monta contexto (§9.5 + histórico + estado do pipeline) | |
| 10 | Motor de IA com tools | |
| 11 | Envia resposta pelo adapter do canal ativo | Respeita capabilities (§14.3) |
| 12 | Atualiza lead, status, interesse e timeline | §9.6 e §9.7 |

### 8.4 Critérios de aceite

| AC | Given / When / Then |
|---|---|
| AC 8.1 | **Given** lead novo escreve fora do horário comercial, **when** a mensagem chega, **then** recebe resposta em até 15s e um lead é criado com status `novo` |
| AC 8.2 | **Given** o lead descreve evento e peça, **when** a IA processa, **then** chama `buscar_produtos` e responde apenas com itens retornados pela API |
| AC 8.3 | **Given** a API da WebLocação retorna erro ou timeout, **when** a IA precisaria do dado, **then** informa que vai confirmar, abre transbordo e não inventa disponibilidade |
| AC 8.4 | **Given** 4 mensagens em 5 segundos, **when** o debounce fecha, **then** a IA responde uma única vez considerando as quatro |
| AC 8.5 | **Given** áudio recebido, **when** processado, **then** é transcrito e tratado como texto |
| AC 8.6 | **Given** conversa pausada por humano, **when** chega mensagem, **then** é persistida e exibida no portal, e a IA não responde |
| AC 8.7 | **Given** a IA gera resposta, **when** enviada, **then** não contém menu numérico nem lista de opções numeradas |

---

## 9. M2 — Identificação, retomada e reengajamento do lead

> **Esta é a seção mais crítica do PRD.** Ela define o que acontece *antes* de qualquer resposta da IA. Toda mensagem que entra na plataforma passa obrigatoriamente por este fluxo, sem exceção de gatilho, canal ou horário.

### 9.1 Princípio

**Nenhuma mensagem existe sem lead.** Independentemente do gatilho da conversa — mensagem espontânea, resposta a campanha, resposta a follow-up, retorno após meses — o telefone é identificado e, se necessário, cadastrado **imediatamente**, antes de qualquer processamento de IA.

O cadastro imediato não depende de:
- a IA conseguir entender a mensagem;
- o lead informar nome, evento ou interesse;
- a conversa prosseguir;
- a integração com a WebLocação estar funcionando.

Se a mensagem chegou, o registro existe.

### 9.2 Campos gravados no cadastro imediato

No momento em que um telefone desconhecido envia a primeira mensagem, o sistema grava **obrigatoriamente**:

| Campo | Origem | Obrigatório |
|---|---|---|
| `contatos.id` | UUID gerado | ✅ |
| `contatos.tenant_id` | Do canal que recebeu | ✅ |
| `contatos.telefone` | Payload normalizado | ✅ |
| `contatos.nome` | `push_name` do WhatsApp, se houver | ⚠️ nullable |
| `contatos.criado_em` | `now()` | ✅ |
| `contatos.ultimo_contato_em` | `now()` | ✅ |
| `leads.id` | UUID gerado | ✅ |
| `leads.contato_id` | FK do contato | ✅ |
| `leads.status` | `'novo'` | ✅ |
| `leads.origem` | Inferida (§9.9) | ✅ |
| `leads.lead_seq` | `1` (primeiro lead deste contato) | ✅ |
| `leads.criado_em` | `now()` | ✅ |
| `leads.ultimo_contato_em` | `now()` | ✅ |
| `lead_eventos` | Registro `lead_criado` | ✅ |

Campos de interesse (`evento_tipo`, `evento_data`, `peca_interesse`, `tamanho`, `cor`, `valor_estimado`) começam nulos e são preenchidos pela IA via `atualizar_lead` conforme a conversa revela.

### 9.3 Fluxo de identificação

```
mensagem chega
   │
   ├─ normaliza telefone (só dígitos + DDI 55)
   │
   ├─ busca contato por (tenant_id, telefone)
   │
   ├── NÃO EXISTE ────────────────────────────────────┐
   │                                                   │
   │   cria contato + lead (status='novo', seq=1)      │
   │   registra 'lead_criado' na timeline              │
   │   contexto_ia = { primeiro_contato: true }        │
   │                                                   │
   └── EXISTE ──────────────────────────────────────┐  │
       │                                             │  │
       ├─ busca lead mais recente do contato         │  │
       │                                             │  │
       ├── lead ATIVO (não ganho/descartado)         │  │
       │   │                                          │  │
       │   ├─ silêncio < 7 dias → CONTINUAÇÃO        │  │
       │   │    reusa o lead, mantém interesse        │  │
       │   │    contexto = histórico completo         │  │
       │   │                                          │  │
       │   └─ silêncio ≥ 7 dias → RETOMADA           │  │
       │        reusa o lead, marca reaberto_em       │  │
       │        contexto = histórico + resumo         │  │
       │        IA confere se o interesse mudou       │  │
       │                                             │  │
       └── lead FECHADO (ganho ou descartado)        │  │
           │                                          │  │
           └─ REENGAJAMENTO                           │  │
                cria NOVO lead (seq = anterior+1)     │  │
                vincula reaberto_de_lead_id           │  │
                herda tags do contato                 │  │
                contexto = resumo do lead anterior    │  │
                IA confere se é o mesmo interesse     │  │
                                                      │  │
   ◀──────────────────────────────────────────────────┘  │
   ◀─────────────────────────────────────────────────────┘
   │
   segue para debounce e motor de IA
```

### 9.4 Matriz de decisão

| Situação do contato | Situação do último lead | Silêncio | Ação | Status resultante |
|---|---|---|---|---|
| Não existe | — | — | Cria contato + lead | `novo` |
| Existe | Ativo | < 7 dias | **Continuação** — reusa o lead | Mantém o atual |
| Existe | Ativo | ≥ 7 dias | **Retomada** — reusa o lead, marca `reaberto_em` | Mantém, IA reavalia |
| Existe | `ganho` | qualquer | **Reengajamento** — novo lead | `novo` |
| Existe | `descartado` | qualquer | **Reengajamento** — novo lead | `novo` |
| Existe | Nenhum lead (contato órfão de campanha) | — | Cria lead | `novo` |
| Existe, `opt_out = true` | qualquer | — | Cria lead e **reverte opt-out** (§15.1) | `novo` |

**Janela de retomada:** 7 dias é o padrão, configurável por tenant em `ia_config.janela_retomada_dias` (mínimo 1, máximo 90).

### 9.5 Contexto entregue à IA

Em toda invocação, o motor recebe um bloco de contexto estruturado — nunca só o texto da mensagem:

```json
{
  "tipo_entrada": "primeiro_contato | continuacao | retomada | reengajamento",
  "contato": {
    "nome": "Marcela Prado",
    "telefone": "5585988124477",
    "primeiro_contato_em": "2026-05-02",
    "total_leads": 2,
    "tags": {"evento":"casamento","mes_evento":"09","papel":"noiva"}
  },
  "lead_atual": {
    "id": "uuid", "seq": 2, "status": "orcamento",
    "evento_tipo": "Casamento", "evento_data": "2026-09-12",
    "peca_interesse": "Vestido longo", "tamanho": "42",
    "valor_estimado": 520,
    "dias_em_silencio": 9,
    "followup_tentativas": 1
  },
  "lead_anterior": {
    "seq": 1, "status_final": "descartado",
    "motivo": "alugou em outro lugar",
    "evento_tipo": "Formatura", "evento_data": "2025-11-28",
    "peca_interesse": "Vestido longo 42",
    "encerrado_em": "2025-11-10"
  },
  "historico_recente": [ /* últimas 20 mensagens */ ],
  "resumo_conversa_anterior": "Procurava vestido longo para formatura em nov/25, orçamento de R$ 465, não fechou.",
  "agendamentos": [ {"tipo":"prova","data":"2026-08-08","hora":"14:00","status":"ativo"} ]
}
```

### 9.6 Reavaliação de interesse

Nos tipos `retomada` e `reengajamento`, a IA é obrigada a verificar se o interesse continua o mesmo antes de prosseguir com qualquer consulta de produto.

**Sinais de mudança de interesse:**

| Sinal | Consequência |
|---|---|
| Evento diferente (era formatura, agora casamento) | Novo interesse — grava versão nova em `lead_interesses` |
| Data do evento diferente | Novo interesse |
| Categoria de peça diferente | Novo interesse |
| Tamanho ou cor diferente, mesmo evento | Atualização do interesse vigente |
| Lead confirma que é o mesmo | Mantém interesse, segue de onde parou |

**Regra de criação de lead na mudança:** se o **evento** mudou (tipo ou data), o lead atual é encerrado como `descartado` com motivo `interesse_substituido` e um novo lead é criado. Se apenas peça, tamanho ou cor mudaram, o lead vigente é atualizado e uma nova linha entra em `lead_interesses`.

**Comportamento conversacional esperado:** a IA reconhece sem interrogar. Não faz checklist, não pede confirmação de dados já conhecidos. Exemplo de retomada correta:

> "Oi Marcela! Você tinha visto o Longo Champanhe pro casamento de setembro. Ainda é isso ou mudou alguma coisa?"

E não:

> "Olá! Para prosseguir, confirme: nome completo, tipo de evento, data do evento e peça de interesse."

### 9.7 Movimentação automática de status pela IA

A IA move o card conforme o teor da conversa, via tool `mover_status`. Toda movimentação grava `lead_eventos` com `autor = 'ia'` e o motivo.

| Status atual | Gatilho no teor da conversa | Status destino |
|---|---|---|
| `novo` | Lead informa evento, data ou tipo de peça | `qualificando` |
| `novo` | Lead pede humano ou assunto crítico | mantém + transbordo |
| `qualificando` | IA apresenta produtos com valores | `orcamento` |
| `qualificando` | Lead demonstra desistência | `descartado` |
| `orcamento` | Lead responde com interesse, pergunta, negocia | `negociando` |
| `orcamento` | Silêncio ≥ janela configurada (worker, não IA) | `follow_up` |
| `follow_up` | Lead responde qualquer coisa | `negociando` |
| `follow_up` | 3 tentativas sem resposta (worker) | `descartado` |
| `negociando` | Agendamento criado com sucesso | `agendado` |
| `negociando` | Lead demonstra desistência | `descartado` |
| `agendado` | Lojista marca contrato fechado (manual) | `ganho` |
| `agendado` | Lead cancela e não remarca | `descartado` |
| qualquer | Lead diz explicitamente que desistiu / já resolveu | `descartado` |

**Restrições da movimentação automática:**

| # | Restrição |
|---|---|
| MV1 | A IA **nunca** move para `ganho`. Só o humano marca contrato fechado |
| MV2 | A IA **nunca** move um lead para trás no pipeline, exceto `follow_up → negociando` |
| MV3 | Se um humano moveu o card manualmente nas últimas 24h, a IA **não sobrescreve** — registra a divergência na timeline e mantém o status humano |
| MV4 | Toda movimentação automática é reversível pelo humano, sem restrição |
| MV5 | Movimentação para `descartado` por desistência exige motivo textual registrado |
| MV6 | Se a IA está indecisa entre dois status, mantém o atual e registra nota na timeline |

### 9.8 Detecção de desistência

A IA classifica como desistência apenas sinais **explícitos**. Silêncio nunca é desistência — silêncio é follow-up.

| Classifica como desistência | Não classifica |
|---|---|
| "já aluguei em outro lugar" | "vou pensar" |
| "desisti", "não vou mais" | "depois eu vejo" |
| "achei mais barato em outro lugar" | "tá caro" |
| "o evento foi cancelado" | não responder |
| "não tenho interesse", "para de me mandar mensagem" | "obrigada" isolado |

"para de me mandar mensagem" e variações também acionam **opt-out** (§15.1), além do descarte.

### 9.9 Inferência de origem

| Origem | Como é inferida |
|---|---|
| `campanha` | Mensagem é resposta a um envio de campanha (correlação por `wa_message_id` de contexto ou janela de 48h após envio) |
| `indicacao` | Lead menciona ter sido indicado por alguém |
| `instagram` | Lead menciona Instagram, ou o link de origem do WhatsApp indica |
| `google` | Lead menciona ter achado no Google/site |
| `manual` | Cadastrado por um humano no portal |
| `whatsapp_organico` | Padrão quando nenhuma das anteriores se aplica |

A origem é gravada uma vez na criação do lead e **não muda** durante o ciclo de vida daquele lead. Um novo lead do mesmo contato pode ter origem diferente.

### 9.10 Critérios de aceite

| AC | Given / When / Then |
|---|---|
| AC 9.1 | **Given** telefone desconhecido, **when** envia qualquer mensagem, **then** contato e lead são criados com id, telefone, data e status `novo` **antes** do debounce, e a timeline registra `lead_criado` |
| AC 9.2 | **Given** telefone desconhecido cuja mensagem a IA não consegue interpretar, **when** processada, **then** o lead existe mesmo assim com status `novo` |
| AC 9.3 | **Given** contato com lead ativo e silêncio de 2 dias, **when** envia mensagem, **then** o mesmo lead é reusado, `tipo_entrada = continuacao`, e o interesse não é reperguntado |
| AC 9.4 | **Given** contato com lead ativo e silêncio de 9 dias, **when** envia mensagem, **then** `tipo_entrada = retomada`, `reaberto_em` é gravado, e a IA menciona o interesse anterior na primeira resposta |
| AC 9.5 | **Given** contato cujo último lead está `descartado`, **when** envia mensagem, **then** um novo lead é criado com `lead_seq` incrementado e `reaberto_de_lead_id` apontando para o anterior |
| AC 9.6 | **Given** retomada em que o lead informa evento diferente do anterior, **when** a IA processa, **then** o lead anterior é encerrado com motivo `interesse_substituido` e um novo lead é criado |
| AC 9.7 | **Given** retomada em que muda só o tamanho, **when** a IA processa, **then** o lead vigente é atualizado e uma nova linha entra em `lead_interesses`, sem criar lead novo |
| AC 9.8 | **Given** lead em `novo` que informa o evento, **when** a IA processa, **then** o card move para `qualificando` com `lead_eventos.autor = 'ia'` |
| AC 9.9 | **Given** um humano moveu o card há 3 horas, **when** a IA tentaria mover para outro status, **then** o status humano é mantido e a divergência é registrada na timeline |
| AC 9.10 | **Given** lead diz "já aluguei em outro lugar", **when** a IA classifica, **then** o lead é descartado imediatamente com motivo textual e sai do quadro |
| AC 9.11 | **Given** lead não responde há 3 dias, **when** o worker avalia, **then** ele **não** é classificado como desistência — vai para `follow_up` |
| AC 9.12 | **Given** a IA tenta mover para `ganho`, **when** a tool é chamada, **then** a operação é rejeitada server-side (MV1) |
| AC 9.13 | **Given** contato que respondeu a uma campanha, **when** o lead é criado, **then** `origem = 'campanha'` |
| AC 9.14 | **Given** contato em opt-out que volta a escrever espontaneamente, **when** a mensagem chega, **then** o opt-out é revertido e um lead é criado |

---

## 10. M3 — CRM Kanban

### 10.1 Colunas

| # | Status | Entra quando | Sai quando |
|---|---|---|---|
| 1 | `novo` | Primeiro contato registrado | IA identifica evento/peça |
| 2 | `qualificando` | Evento, data ou estilo identificado | Valores apresentados |
| 3 | `orcamento` | Produtos e valores enviados | Lead responde, agenda ou esfria |
| 4 | `follow_up` | Silêncio além da janela | Lead responde ou é descartado |
| 5 | `negociando` | Lead retomou a conversa | Agenda prova ou desiste |
| 6 | `agendado` | Agendamento criado na WebLocação | Ganho ou descartado |
| 7 | `ganho` | Lojista marca contrato fechado | Arquiva após 30 dias |
| 8 | `descartado` | Desistência, descarte manual ou tentativas esgotadas | Sai do quadro, fica na base |

### 10.2 Regra de follow-up

| Parâmetro | Padrão | Faixa |
|---|---|---|
| `janela_silencio_horas` | 24 | 4–168 |
| `max_tentativas` | 3 | 1–5 |
| `intervalo_tentativas_horas` | 48 | 12–168 |
| `disparo_automatico` | `false` | bool |

Lead em `orcamento`, `qualificando` ou `negociando` sem resposta há `janela_silencio_horas` → move para `follow_up` e o **botão de disparo fica ativo**. O lojista escolhe a mensagem e dispara com um clique.

- Lead responde → `negociando`, contador zera.
- `max_tentativas` atingido → `descartado` automático com motivo `sem_resposta`.
- Desistência explícita → `descartado` imediato.

**Interação com a janela de 24h (canal Meta):** se a janela estiver fechada, o disparo de follow-up só é permitido via template aprovado. A UI indica isso no modal e desabilita mensagens sem `template_meta` correspondente.

### 10.3 Descarte com retenção

Ao descartar, o card sai do quadro visual mas:
- o lead permanece em `leads` com `status='descartado'` e motivo;
- o contato permanece em `contatos` com histórico e tags;
- fica elegível para campanhas (§15) e para reengajamento (§9.4).

### 10.4 Timeline

Toda alteração relevante gera `lead_eventos`: criação, mudança de status (com autor), follow-up enviado, agendamento criado, transbordo aberto/fechado, interesse alterado, descarte, nota manual.

### 10.5 Critérios de aceite

| AC | Given / When / Then |
|---|---|
| AC 10.1 | **Given** lead em `orcamento` sem responder há 24h, **when** o worker roda, **then** o card move para `follow_up` e o botão de disparo aparece ativo |
| AC 10.2 | **Given** o lojista dispara uma mensagem escolhida, **when** confirma, **then** ela é enviada pelo canal ativo e registrada na timeline |
| AC 10.3 | **Given** o lead responde após o follow-up, **then** o card move para `negociando` e o contador zera |
| AC 10.4 | **Given** 3 follow-ups sem resposta, **then** o lead é descartado e sai do quadro, permanecendo em contatos |
| AC 10.5 | **Given** o lojista arrasta um card, **then** o status é persistido com `autor='humano'` e `autor_user_id` |
| AC 10.6 | **Given** canal Meta com janela fechada, **when** o lojista abre o modal de follow-up, **then** só mensagens com template aprovado são selecionáveis |
| AC 10.7 | **Given** lead descartado, **when** o lojista abre a base, **then** ele aparece com suas tags |

---

## 11. M4 — Agenda

Somente leitura. Dados vêm da WebLocação e dos agendamentos criados pela automação.

**Funcionalidades:** seletor de período (dia, semana, mês, intervalo customizado); filtro por tipo e origem (automação vs. loja); link para o lead correspondente.

**Regra:** qualquer alteração é feita no portal da WebLocação. Aviso explícito visível na tela. Sync a cada 10 minutos e sob demanda.

| AC | Given / When / Then |
|---|---|
| AC 11.1 | **Given** o usuário escolhe um período, **then** só os agendamentos daquele intervalo são exibidos |
| AC 11.2 | **Given** um agendamento criado pela automação, **then** ele aparece marcado com origem `automação` |
| AC 11.3 | **Given** o lojista altera algo no ERP, **when** o sync roda, **then** a alteração reflete no ALFAIA em até 10 minutos |
| AC 11.4 | **Given** a tela de agenda, **then** o aviso de que alterações são feitas no portal da WebLocação está visível sem scroll |

---

## 12. M5 — Consulta de produtos

Sem catálogo local, sem tela de acervo. A consulta acontece dentro da conversa (acionada pela IA) e como painel de apoio no portal (para o atendente consultar o mesmo que a IA consulta).

**O que o lead pode expressar:** tipo de evento, papel (noiva, madrinha, padrinho), estilo (longo, sereia, princesa, slim, clássico), peça por código ou nome, cor, tamanho, data.

**Resultado:** até 5 itens por resposta, com foto, nome, tamanho, cor e valor. Nada é persistido além do log da chamada.

| AC | Given / When / Then |
|---|---|
| AC 12.1 | **Given** o lead expressa evento e estilo, **then** a IA chama `buscar_produtos` traduzindo a linguagem natural em filtros |
| AC 12.2 | **Given** a API retorna 12 itens, **then** a IA apresenta no máximo 5, priorizando os mais aderentes |
| AC 12.3 | **Given** a API retorna 0 itens, **then** a IA informa a indisponibilidade e oferece alternativa (outra data ou outro estilo), sem inventar peça |
| AC 12.4 | **Given** qualquer consulta, **then** nenhum produto é gravado em tabela local |

---

## 13. M6 — Transbordo

### 13.1 Gatilhos

| Gatilho | Origem |
|---|---|
| Lead pede humano explicitamente | Lead |
| IA classifica assunto como crítico (reclamação, avaria, urgência, jurídico) | IA |
| IA não resolve após 3 tentativas no mesmo ponto | IA |
| Falha de integração em ponto crítico | Sistema |
| Atendente assume por vontade própria | Humano |

### 13.2 Comportamento

- Transbordo aberto → card marcado, fila notificada em realtime.
- **Assumir** → IA pausada por tempo configurável (padrão 30 min, renovável a cada mensagem do atendente).
- Atendente responde pelo portal; envio pelo canal ativo.
- **Devolver para a automação** → pausa encerrada, IA volta na próxima mensagem do lead.
- Pausa expirada sem ação → IA retoma automaticamente e registra na timeline.

| AC | Given / When / Then |
|---|---|
| AC 13.1 | **Given** o lead pede atendente, **then** o transbordo abre, a IA envia acolhimento e para de responder |
| AC 13.2 | **Given** o atendente assume, **then** a IA fica pausada e o campo de resposta é liberado |
| AC 13.3 | **Given** o atendente devolve, **then** a IA volta a responder na mensagem seguinte |
| AC 13.4 | **Given** pausa expirada sem ação, **when** chega mensagem, **then** a IA responde e a timeline registra a retomada automática |
| AC 13.5 | **Given** conversa em transbordo, **then** a mensagem do lead é persistida e o pipeline não é movido automaticamente |

---

## 14. M7 — Canal WhatsApp dual

### 14.1 Comparativo

| | UAZAPI | Meta Cloud API (BSP) |
|---|---|---|
| Tipo | Não oficial (WhatsApp Web) | Oficial |
| Auth | Token por instância | Bearer reseller + workspace |
| Recebimento | `POST /webhook/{token}` | `forward_to_url` com HMAC |
| Envio texto | `POST /send/text`, header `token` | `POST /workspaces/{id}/messages` |
| Envio mídia | `POST /send/media` | `POST /workspaces/{id}/messages/media` |
| Janela 24h | Não se aplica | **Se aplica** |
| Anti-ban | `delay` + `presence: composing` | Não se aplica |
| Risco de banimento | Existe | Praticamente nulo |

> **Nota de implementação (do contrato UAZAPI documentado):** os headers do UAZAPI são inconsistentes entre endpoints — `token` em `/send/text` e `apikey` em `/message/sendMedia/{instance}`. O adapter deve encapsular essa diferença; nenhuma camada acima pode saber disso.

### 14.2 Interface do adapter

```python
class CanalAdapter(Protocol):
    def normalizar_webhook(self, raw: bytes, headers: dict) -> list[PayloadNormalizado]: ...
    async def enviar_texto(self, to: str, text: str) -> ResultadoEnvio: ...
    async def enviar_midia(self, to: str, url: str, tipo: str, caption: str | None) -> ResultadoEnvio: ...
    async def enviar_template(self, to: str, nome: str, idioma: str, componentes: list) -> ResultadoEnvio: ...
    async def marcar_lido(self, wa_message_id: str) -> None: ...
    @property
    def capabilities(self) -> Capabilities: ...
```

```python
@dataclass(frozen=True)
class Capabilities:
    janela_24h: bool          # True = exige janela aberta para texto livre
    suporta_template: bool
    requer_delay: bool
    delay_min_ms: int
    delay_max_ms: int
    exige_horario_comercial: bool
```

### 14.3 Seletor dinâmico

- Cada tenant tem N canais; exatamente um com `ativo = true` (garantido por índice único parcial).
- Troca pela UI com confirmação; vale a partir da próxima mensagem processada.
- Conversas em andamento continuam; histórico preservado independentemente do provider.
- O motor consulta `capabilities` antes de enviar: canal com `janela_24h` e janela fechada → texto livre bloqueado **server-side**, UI orienta ao template.

### 14.4 Segurança do canal

| # | Regra |
|---|---|
| C1 | Webhook Meta: HMAC obrigatório. Inválido → 401 e descarte, sem persistir em conversas |
| C2 | Webhook UAZAPI: identificação por token na URL; rota isenta de auth de sessão (M2M) |
| C3 | Ambos: captura do corpo cru + headers em `webhook_capturas` |
| C4 | Idempotência obrigatória por `wa_message_id` |
| C5 | Resposta 200 imediata, processamento em background |
| C6 | Credenciais apenas server-side |
| C7 | Rota de webhook isenta de rate limit |

### 14.5 Critérios de aceite

| AC | Given / When / Then |
|---|---|
| AC 14.1 | **Given** canal UAZAPI ativo, **then** a mensagem é normalizada no contrato de §6.3 |
| AC 14.2 | **Given** canal Meta ativo, **then** o HMAC é validado e o payload normalizado é estruturalmente idêntico ao do UAZAPI |
| AC 14.3 | **Given** HMAC inválido, **then** responde 401, captura o cru e não persiste em conversas |
| AC 14.4 | **Given** troca de canal ativo, **then** a próxima mensagem sai pelo novo provider sem perda de histórico |
| AC 14.5 | **Given** canal Meta e janela fechada, **when** tenta enviar texto livre, **then** bloqueia server-side com mensagem clara |
| AC 14.6 | **Given** a mesma mensagem chega duas vezes, **then** só uma linha existe em `mensagens` |
| AC 14.7 | **Given** dois canais do mesmo tenant, **when** tenta ativar o segundo sem desativar o primeiro, **then** o índice único impede |

---

## 15. M8 — Base de contatos e campanhas

### 15.1 Base de contatos

Repositório permanente, independente do pipeline. Todo telefone que interagiu entra e nunca sai.

**Segmentação:** tipo de evento, mês/ano do evento, papel, faixa de valor, categoria de peça, status final do último lead, data do último contato, origem.

**Opt-out:** palavra-chave de descadastro processada automaticamente (`STOP`, `PARAR`, "não quero mais receber", "para de me mandar mensagem"). Contato marcado `opt_out = true`, excluído de qualquer campanha.

**Reversão de opt-out:** se o contato voltar a escrever **espontaneamente** (não em resposta a campanha, que não existe para ele), o opt-out é revertido, com registro na timeline. Escrever é consentimento renovado.

### 15.2 Campanhas

**Fluxo:** definir segmento → prévia com contagem e amostra → escolher mensagem → agendar ou disparar → acompanhar entrega e resposta.

| # | Regra de disparo |
|---|---|
| K1 | Canal UAZAPI: delay aleatório 5s–15s; `presence: composing`; horário comercial obrigatório |
| K2 | Canal Meta: template aprovado obrigatório; sem delay artificial |
| K3 | Contato em `opt_out` nunca entra em campanha, sem exceção |
| K4 | Limite de 1 campanha por contato a cada 15 dias (configurável) |
| K5 | Resposta a campanha cria ou reabre lead com origem `campanha` (§9.4) |
| K6 | Campanha pausável, com retomada de onde parou |
| K7 | UAZAPI: aquecimento — máx. 200 envios/dia nos primeiros 7 dias de um número novo |
| K8 | Se a taxa de falha ultrapassar 15% em 50 envios, a campanha pausa automaticamente e alerta |

### 15.3 Critérios de aceite

| AC | Given / When / Then |
|---|---|
| AC 15.1 | **Given** lead descartado, **when** o lojista filtra a base, **then** ele aparece com suas tags |
| AC 15.2 | **Given** campanha com segmento, **when** pede prévia, **then** vê contagem exata e amostra |
| AC 15.3 | **Given** canal UAZAPI, **then** o intervalo entre envios é aleatório 5–15s e só ocorre em horário comercial |
| AC 15.4 | **Given** contato em opt-out, **then** não é incluído em nenhuma campanha |
| AC 15.5 | **Given** contato responde à campanha, **then** um lead é criado/reaberto com origem `campanha` |
| AC 15.6 | **Given** 15% de falha em 50 envios, **then** a campanha pausa automaticamente e alerta o lojista |
| AC 15.7 | **Given** contato em opt-out escreve espontaneamente, **then** o opt-out é revertido com registro |

---

## 16. M9 — Automações

| # | Chave | Gatilho | Ação |
|---|---|---|---|
| 1 | `atendimento` | Mensagem nova | Responde, qualifica e registra o lead |
| 2 | `identificacao` | Toda mensagem | Identifica, cria ou retoma o lead (§9) — **não desligável** |
| 3 | `disponibilidade` | Lead expressa desejo | Busca na WebLocação e apresenta |
| 4 | `agendamento` | Lead aceita marcar | Consulta slots e grava agendamento |
| 5 | `followup` | Silêncio além da janela | Move para `follow_up` e habilita disparo |
| 6 | `descarte` | Desistência ou tentativas esgotadas | Descarta e retém na base |
| 7 | `transbordo` | Pedido ou classificação crítica | Abre transbordo e pausa IA |
| 8 | `campanha` | Manual ou agendada | Dispara respeitando K1–K8 |

A automação `identificacao` é estrutural e não pode ser desligada pela UI — desligá-la quebraria P5 e P8.

Cada execução registra em `automacao_execucoes`: tenant, chave, lead, entrada, resultado, latência, erro.

---

## 17. Modelo de dados

### 17.1 Enums

```sql
create type lead_status as enum (
  'novo','qualificando','orcamento','follow_up','negociando','agendado','ganho','descartado'
);
create type lead_origem as enum (
  'whatsapp_organico','instagram','indicacao','google','campanha','manual'
);
create type canal_provider as enum ('uazapi','meta');
create type remetente as enum ('lead','ia','atendente','sistema');
create type conversa_estado as enum ('ia','pausada','transbordo');
create type tipo_entrada as enum ('primeiro_contato','continuacao','retomada','reengajamento');
```

### 17.2 Tenancy

```sql
create table tenants (
  id uuid primary key default gen_random_uuid(),
  nome text not null,
  slug text unique not null,
  cidade text, uf text,
  ativo boolean not null default true,
  criado_em timestamptz not null default now()
);

create table tenant_membros (
  tenant_id uuid not null references tenants(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  papel text not null default 'atendente',   -- dono | atendente | operador
  primary key (tenant_id, user_id)
);
```

### 17.3 Canal

```sql
create table canais (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  provider canal_provider not null,
  nome text not null,
  ativo boolean not null default false,
  uazapi_base_url text,
  uazapi_instancia text,
  uazapi_token text,
  meta_workspace_id text,
  meta_phone_number_id text,
  meta_waba_id text,
  meta_forward_secret text,
  status text default 'desconectado',
  qualidade text,
  aquecimento_iniciado_em date,
  criado_em timestamptz not null default now()
);
create unique index canais_um_ativo on canais(tenant_id) where ativo;

create table webhook_capturas (
  id bigserial primary key,
  tenant_id uuid references tenants(id) on delete set null,
  provider canal_provider,
  metodo text, url text,
  headers jsonb, corpo text,
  hmac_ok boolean,
  criado_em timestamptz not null default now()
);
```

### 17.4 Contatos e leads

```sql
create table contatos (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  telefone text not null,
  nome text,
  tags jsonb not null default '{}'::jsonb,
  opt_out boolean not null default false,
  opt_out_em timestamptz,
  opt_out_revertido_em timestamptz,
  total_leads int not null default 0,
  primeiro_contato_em timestamptz not null default now(),
  ultimo_contato_em timestamptz,
  criado_em timestamptz not null default now(),
  unique (tenant_id, telefone)
);
create index contatos_tel on contatos(tenant_id, telefone);

create table leads (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  contato_id uuid not null references contatos(id) on delete cascade,
  lead_seq int not null default 1,
  status lead_status not null default 'novo',
  origem lead_origem not null default 'whatsapp_organico',
  evento_tipo text,
  evento_data date,
  papel text,
  peca_interesse text,
  tamanho text,
  cor text,
  valor_estimado numeric(10,2),
  followup_tentativas int not null default 0,
  followup_proximo_em timestamptz,
  reaberto_em timestamptz,
  reaberto_de_lead_id uuid references leads(id) on delete set null,
  status_alterado_em timestamptz not null default now(),
  status_alterado_por remetente not null default 'sistema',
  motivo_descarte text,
  ganho_em timestamptz,
  ultimo_contato_em timestamptz not null default now(),
  atualizado_em timestamptz not null default now(),
  criado_em timestamptz not null default now(),
  unique (contato_id, lead_seq)
);
create index leads_board on leads(tenant_id, status, atualizado_em desc);
create index leads_followup on leads(tenant_id, followup_proximo_em)
  where status in ('orcamento','qualificando','negociando','follow_up');
create index leads_contato_atual on leads(contato_id, criado_em desc);

-- Histórico de interesse: nunca sobrescrito (A10)
create table lead_interesses (
  id bigserial primary key,
  tenant_id uuid not null references tenants(id) on delete cascade,
  lead_id uuid not null references leads(id) on delete cascade,
  versao int not null default 1,
  evento_tipo text, evento_data date, papel text,
  peca_interesse text, tamanho text, cor text,
  valor_estimado numeric(10,2),
  motivo text,                       -- inicial | atualizacao | substituicao
  criado_em timestamptz not null default now(),
  unique (lead_id, versao)
);

create table lead_eventos (
  id bigserial primary key,
  tenant_id uuid not null references tenants(id) on delete cascade,
  lead_id uuid not null references leads(id) on delete cascade,
  tipo text not null,   -- lead_criado | status_mudou | interesse_alterado | followup_enviado
                        -- | transbordo_aberto | transbordo_assumido | transbordo_devolvido
                        -- | agendou | descartado | reaberto | divergencia_ia_humano | nota
  de text, para text,
  autor remetente not null default 'sistema',
  autor_user_id uuid references auth.users(id),
  motivo text,
  detalhe jsonb,
  criado_em timestamptz not null default now()
);
create index lead_eventos_lead on lead_eventos(lead_id, criado_em desc);
```

### 17.5 Conversas

```sql
create table conversas (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  canal_id uuid not null references canais(id) on delete cascade,
  contato_id uuid not null references contatos(id) on delete cascade,
  lead_id uuid references leads(id) on delete set null,
  estado conversa_estado not null default 'ia',
  pausada_ate timestamptz,
  pausada_por uuid references auth.users(id),
  ultima_entrada_em timestamptz,      -- base da janela de 24h
  ultima_mensagem_em timestamptz,
  nao_lidas int not null default 0,
  criado_em timestamptz not null default now(),
  unique (canal_id, contato_id)
);

create table mensagens (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  conversa_id uuid not null references conversas(id) on delete cascade,
  lead_id uuid references leads(id) on delete set null,
  wa_message_id text,
  remetente remetente not null,
  autor_user_id uuid references auth.users(id),
  tipo text not null default 'text',
  conteudo text,
  midia_url text,
  status text,                        -- sent | delivered | read | failed
  metadata jsonb,
  criado_em timestamptz not null default now()
);
create unique index mensagens_wamid on mensagens(wa_message_id) where wa_message_id is not null;
create index mensagens_conversa on mensagens(conversa_id, criado_em desc);
```

### 17.6 Debounce

```sql
create table debounce_buffer (
  id bigserial primary key,
  tenant_id uuid not null,
  conversa_id uuid not null references conversas(id) on delete cascade,
  processar_em timestamptz not null,
  bloqueado_em timestamptz,
  criado_em timestamptz not null default now()
);
create unique index debounce_um_por_conversa on debounce_buffer(conversa_id)
  where bloqueado_em is null;
```

Consumo:

```sql
select * from debounce_buffer
where processar_em <= now() and bloqueado_em is null
order by processar_em
for update skip locked
limit 20;
```

### 17.7 Agenda e integração

```sql
create table agendamentos (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  wl_agendamento_id text,
  lead_id uuid references leads(id) on delete set null,
  tipo text not null,
  data date not null,
  hora time not null,
  cliente_nome text,
  cliente_telefone text,
  produto_ref text,
  origem text not null default 'automacao',
  status text not null default 'ativo',
  sincronizado_em timestamptz not null default now(),
  unique (tenant_id, wl_agendamento_id)
);
create index agendamentos_periodo on agendamentos(tenant_id, data, hora);

create table wl_integracao (
  tenant_id uuid primary key references tenants(id) on delete cascade,
  base_url text not null,
  api_key text not null,
  loja_ref text,
  modo text not null default 'mock',   -- mock | real
  ativa boolean not null default true,
  ultimo_sync_em timestamptz
);

create table wl_chamadas (
  id bigserial primary key,
  tenant_id uuid not null references tenants(id) on delete cascade,
  metodo text, rota text,
  status_code int, latencia_ms int,
  erro text,
  criado_em timestamptz not null default now()
);
```

### 17.8 Automações, follow-up e campanhas

```sql
create table automacoes (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  chave text not null,
  ativa boolean not null default true,
  config jsonb not null default '{}'::jsonb,
  unique (tenant_id, chave)
);

create table automacao_execucoes (
  id bigserial primary key,
  tenant_id uuid not null references tenants(id) on delete cascade,
  chave text not null,
  lead_id uuid references leads(id) on delete set null,
  resultado text, latencia_ms int, erro text,
  criado_em timestamptz not null default now()
);

create table mensagens_followup (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  nome text not null,
  corpo text not null,               -- {{nome}}, {{evento}}, {{peca}}
  template_meta text,
  ativa boolean not null default true
);

create table campanhas (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  nome text not null,
  segmento jsonb not null,
  mensagem_id uuid references mensagens_followup(id),
  status text not null default 'rascunho',
  agendada_para timestamptz,
  total int not null default 0,
  enviados int not null default 0,
  falhas int not null default 0,
  respondidos int not null default 0,
  pausada_motivo text,
  criado_em timestamptz not null default now()
);

create table campanha_alvos (
  id bigserial primary key,
  campanha_id uuid not null references campanhas(id) on delete cascade,
  contato_id uuid not null references contatos(id) on delete cascade,
  status text not null default 'pendente',
  wa_message_id text,
  enviado_em timestamptz,
  unique (campanha_id, contato_id)
);
```

### 17.9 IA

```sql
create table ia_config (
  tenant_id uuid primary key references tenants(id) on delete cascade,
  persona_nome text not null default 'Atendente',
  prompt_sistema text not null,
  modelo text not null default 'claude-sonnet-4-6',
  temperatura numeric(2,1) not null default 0.3,
  janela_retomada_dias int not null default 7 check (janela_retomada_dias between 1 and 90),
  janela_silencio_horas int not null default 24,
  max_tentativas_followup int not null default 3,
  intervalo_tentativas_horas int not null default 48,
  disparo_followup_automatico boolean not null default false,
  pausa_transbordo_minutos int not null default 30,
  horario_comercial jsonb not null default '{"inicio":"09:00","fim":"18:00","dias":[1,2,3,4,5,6]}'::jsonb
);
```

### 17.10 Função de identificação

Implementa §9.3 de forma atômica, evitando corrida entre processos:

```sql
create or replace function identificar_lead(
  p_tenant uuid, p_telefone text, p_push_name text, p_origem lead_origem
) returns table (contato_id uuid, lead_id uuid, entrada tipo_entrada)
language plpgsql as $$
declare
  v_contato uuid; v_lead uuid; v_status lead_status;
  v_ultimo timestamptz; v_seq int; v_janela int; v_entrada tipo_entrada;
begin
  select janela_retomada_dias into v_janela from ia_config where tenant_id = p_tenant;
  v_janela := coalesce(v_janela, 7);

  insert into contatos (tenant_id, telefone, nome)
  values (p_tenant, p_telefone, p_push_name)
  on conflict (tenant_id, telefone) do update
    set ultimo_contato_em = now(),
        nome = coalesce(contatos.nome, excluded.nome)
  returning id into v_contato;

  select id, status, ultimo_contato_em, lead_seq
    into v_lead, v_status, v_ultimo, v_seq
  from leads where contato_id = v_contato
  order by criado_em desc limit 1;

  if v_lead is null then
    v_entrada := 'primeiro_contato';
  elsif v_status in ('ganho','descartado') then
    v_entrada := 'reengajamento';
  elsif now() - v_ultimo >= (v_janela || ' days')::interval then
    v_entrada := 'retomada';
  else
    v_entrada := 'continuacao';
  end if;

  if v_entrada in ('primeiro_contato','reengajamento') then
    insert into leads (tenant_id, contato_id, lead_seq, origem, reaberto_de_lead_id)
    values (p_tenant, v_contato, coalesce(v_seq,0)+1, p_origem,
            case when v_entrada='reengajamento' then v_lead else null end)
    returning id into v_lead;

    update contatos set total_leads = total_leads + 1 where id = v_contato;

    insert into lead_eventos (tenant_id, lead_id, tipo, para, autor, detalhe)
    values (p_tenant, v_lead, 'lead_criado', 'novo', 'sistema',
            jsonb_build_object('entrada', v_entrada));
  else
    update leads
      set ultimo_contato_em = now(),
          reaberto_em = case when v_entrada='retomada' then now() else reaberto_em end
      where id = v_lead;

    if v_entrada = 'retomada' then
      insert into lead_eventos (tenant_id, lead_id, tipo, autor, detalhe)
      values (p_tenant, v_lead, 'reaberto', 'sistema',
              jsonb_build_object('dias_silencio', extract(day from now() - v_ultimo)));
    end if;
  end if;

  return query select v_contato, v_lead, v_entrada;
end $$;
```

### 17.11 RLS

Todas as tabelas com `tenant_id` recebem RLS e policy por pertencimento:

```sql
alter table leads enable row level security;
create policy leads_tenant on leads for all
  using  (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()))
  with check (tenant_id in (select tenant_id from tenant_membros where user_id = auth.uid()));
```

O worker acessa via service role, com filtro explícito por `tenant_id` em toda query. Webhooks são rotas M2M isentas de auth de sessão.

### 17.12 Realtime

Habilitado em `conversas`, `mensagens`, `leads` e `lead_eventos`.

---

## 18. API interna

### 18.1 Worker (FastAPI)

| Método | Rota | Auth | Descrição |
|---|---|---|---|
| POST | `/webhook/uazapi/{token}` | Token na URL | Recebe eventos UAZAPI |
| POST | `/webhook/meta/{canal_id}` | HMAC | Recebe eventos Meta |
| GET | `/webhook/meta/{canal_id}` | — | Handshake (`hub.challenge`) |
| POST | `/enviar` | `x-internal-token` | Envio a partir do portal (atendente) |
| POST | `/followup/disparar` | `x-internal-token` | Dispara follow-up escolhido |
| POST | `/campanha/{id}/iniciar` | `x-internal-token` | Inicia campanha |
| POST | `/campanha/{id}/pausar` | `x-internal-token` | Pausa campanha |
| GET | `/health` | — | Liveness |

### 18.2 Portal (Next.js route handlers)

| Método | Rota | Permissão |
|---|---|---|
| GET | `/api/leads` | `lead:read` |
| PATCH | `/api/leads/{id}` | `lead:update` |
| POST | `/api/leads/{id}/descartar` | `lead:update` |
| POST | `/api/leads/{id}/followup` | `followup:create` |
| GET | `/api/conversas/{id}/mensagens` | `atendimento:read` |
| POST | `/api/conversas/{id}/assumir` | `atendimento:update` |
| POST | `/api/conversas/{id}/devolver` | `atendimento:update` |
| GET | `/api/agenda?inicio=&fim=` | `agenda:read` |
| POST | `/api/agenda/sync` | `agenda:update` |
| GET | `/api/produtos?...` | `produto:read` |
| GET | `/api/contatos?segmento=` | `contato:read` |
| POST | `/api/campanhas` | `campanha:create` |
| PATCH | `/api/canais/{id}/ativar` | `canal:update` |
| PATCH | `/api/automacoes/{chave}` | `automacao:update` |

### 18.3 Jobs agendados

| Job | Frequência | Ação |
|---|---|---|
| `debounce_worker` | contínuo (loop 2s) | Consome buffer e chama o motor |
| `followup_scan` | 15 min | Move leads silenciosos para `follow_up` |
| `followup_expirar` | 1 h | Descarta leads com tentativas esgotadas |
| `agenda_sync` | 10 min | Sincroniza agendamentos da WebLocação |
| `campanha_worker` | contínuo | Processa fila de campanhas respeitando K1–K8 |
| `transbordo_expirar` | 5 min | Encerra pausas vencidas |
| `arquivar_ganhos` | diário | Arquiva `ganho` com mais de 30 dias |

---

## 19. Prompt de sistema

### 19.1 Estrutura

O prompt é montado em quatro blocos, nesta ordem: identidade e persona (de `ia_config`) → regras invioláveis → contexto do lead (§9.5) → histórico. Só o primeiro bloco é editável pelo operador; os demais são gerados pelo sistema.

### 19.2 Regras invioláveis (não editáveis)

```
1. Nunca ofereça menu numérico. Nunca peça "digite 1 para...".
2. Nunca informe disponibilidade, horário ou valor que não tenha vindo de uma
   chamada de ferramenta nesta conversa. Se a ferramenta falhar, diga que vai
   confirmar e acione abrir_transbordo.
3. Respostas curtas. Sem preâmbulo. Sem repetir o que o lead acabou de dizer.
4. Nunca marque um lead como ganho. Isso é decisão do lojista.
5. Em retomada ou reengajamento, reconheça o interesse anterior de forma natural
   na primeira resposta. Não faça checklist de confirmação de dados.
6. Silêncio não é desistência. Só classifique desistência com sinal explícito.
7. Assunto crítico (avaria, reclamação, urgência, jurídico): não tente resolver,
   não prometa prazo, acione abrir_transbordo.
8. Nunca peça CPF, endereço completo, dados bancários ou foto de documento.
9. Se estiver indeciso entre dois status, mantenha o atual.
10. Escreva em português brasileiro, tom da persona configurada, sem emoji em excesso.
```

### 19.3 Critérios de aceite

| AC | Given / When / Then |
|---|---|
| AC 19.1 | **Given** o operador edita a persona, **then** as regras invioláveis permanecem no prompt final |
| AC 19.2 | **Given** qualquer resposta gerada, **then** não contém solicitação de CPF ou documento |
| AC 19.3 | **Given** entrada do tipo `retomada`, **then** a primeira resposta referencia o interesse anterior |

---

## 20. Requisitos não funcionais

| # | Requisito | Alvo |
|---|---|---|
| NFR1 | Tempo de primeira resposta ao lead | p95 ≤ 15s |
| NFR2 | Latência do webhook (200 OK) | p99 ≤ 300ms |
| NFR3 | Latência de chamada à WebLocação | p95 ≤ 2s, timeout 8s |
| NFR4 | Disponibilidade da plataforma | ≥ 99% mensal |
| NFR5 | Perda de mensagem inbound | 0 — captura sempre retida |
| NFR6 | Conversas simultâneas por tenant | ≥ 100 |
| NFR7 | Tenants por instância do worker | ≥ 50 |
| NFR8 | Carregamento do Kanban com 500 leads | ≤ 2s |
| NFR9 | Realtime de nova mensagem no portal | ≤ 2s |
| NFR10 | Retenção de mensagens | 24 meses |
| NFR11 | Custo de LLM por conversa resolvida | ≤ R$ 0,40 |
| NFR12 | Acessibilidade do portal | WCAG 2.1 AA nos fluxos principais |
| NFR13 | Portal responsivo | ≥ 360px de largura |

---

## 21. Observabilidade e tratamento de erros

### 21.1 Logs estruturados

Todo log em JSON com: `tenant_id`, `canal_id`, `conversa_id`, `lead_id`, `wa_message_id`, `etapa`, `latencia_ms`, `resultado`, `erro`.

### 21.2 Matriz de erros

| Cenário | Comportamento | Visível ao lead | Alerta |
|---|---|---|---|
| WebLocação 5xx | Retry 2× com backoff; falhou → transbordo | "Vou confirmar e já te falo" | Sim |
| WebLocação timeout | Igual acima | Igual | Sim |
| WebLocação 4xx | Sem retry; log + transbordo | Igual | Sim |
| LLM indisponível | Retry 1×; falhou → transbordo | "Já te respondo" | Sim |
| LLM devolve tool inválida | Rejeita, reprompt 1×; falhou → transbordo | Nada | Sim |
| Envio falha no canal | Retry 2×; falhou → marca `failed` e alerta portal | Nada | Sim |
| HMAC inválido | 401, captura, sem persistir | Nada | Sim (se recorrente) |
| Mensagem duplicada | Descarta silenciosamente | Nada | Não |
| Transcrição falha | Pede ao lead que escreva | "Não consegui ouvir o áudio, pode escrever?" | Não |
| Banco indisponível | 200 no webhook, captura em fila local, reprocessa | Nada | Sim (crítico) |

### 21.3 Alertas

| Alerta | Condição |
|---|---|
| Canal desconectado | `status != connected` por mais de 5 min |
| Qualidade do número caiu | `quality_rating` diferente de alto |
| Taxa de falha de envio | > 10% em 30 min |
| Transbordo sem atendimento | Aberto há mais de 30 min |
| Integração WL fora | 3 falhas consecutivas |
| Campanha pausada por falha | K8 acionado |

---

## 22. Segurança e LGPD

| # | Requisito |
|---|---|
| S1 | RLS habilitada em todas as tabelas com `tenant_id`; nenhuma policy `using (true)` |
| S2 | Credenciais (tokens de canal, chave WL) apenas server-side, em coluna criptografada ou secret store |
| S3 | Webhooks isentos de auth de sessão, mas protegidos por HMAC ou token na URL |
| S4 | Nenhum dado pessoal em URL ou query string |
| S5 | Auditoria de acesso: toda leitura de base de contatos por exportação é logada |
| S6 | Base legal LGPD: legítimo interesse para atendimento; consentimento para campanha (o lead escreveu primeiro) |
| S7 | Opt-out honrado permanentemente até reversão espontânea pelo titular (§15.1) |
| S8 | Direito de eliminação: rota de exclusão de contato apaga contato, leads, mensagens e alvos de campanha em cascata |
| S9 | Retenção de mensagens: 24 meses; após isso, anonimização do conteúdo mantendo métricas |
| S10 | A IA nunca solicita CPF, endereço completo, dados bancários ou documento |
| S11 | Transcrição de áudio não persiste o arquivo original além de 7 dias |
| S12 | Exportação de dados apenas para papéis `dono` e `operador` |

---

## 23. Testes

### 23.1 Cobertura mínima por camada

| Camada | Tipo | Cobertura |
|---|---|---|
| Adapters de canal | Unitário | Normalização, HMAC, idempotência, headers — 100% dos caminhos |
| `identificar_lead` | Integração (banco real) | Os 7 cenários da matriz §9.4 |
| Motor de IA | Contrato | Toda tool com schema validado; recusa a inventar dado |
| Engine de follow-up | Unitário | Janela, tentativas, zeragem |
| Engine de campanha | Unitário | K1–K8 |
| RLS | Integração | Tentativa de cross-tenant deve falhar |
| Portal | E2E | Kanban drag-drop, assumir/devolver, disparo de follow-up |

### 23.2 Casos de teste obrigatórios de §9

| # | Caso |
|---|---|
| T1 | Telefone novo → contato + lead criados antes do debounce |
| T2 | Mensagem ininteligível de telefone novo → lead existe mesmo assim |
| T3 | Silêncio de 2 dias → `continuacao`, mesmo lead |
| T4 | Silêncio de 9 dias → `retomada`, `reaberto_em` gravado |
| T5 | Último lead `descartado` → `reengajamento`, novo lead com seq+1 |
| T6 | Último lead `ganho` → `reengajamento` |
| T7 | Evento diferente na retomada → lead anterior encerrado, novo criado |
| T8 | Só tamanho muda → mesmo lead, nova versão em `lead_interesses` |
| T9 | Duas mensagens simultâneas do mesmo telefone novo → um único lead (corrida) |
| T10 | IA tenta mover para `ganho` → rejeitado |
| T11 | Humano moveu há 3h → IA não sobrescreve |
| T12 | Contato em opt-out escreve → opt-out revertido |

---

## 24. Ambientes e deploy

> **Emenda 08/08/2026 (@po).** Esta seção estava incompleta: definia os ambientes lógicos (`local`/`producao`) sem declarar em qual infraestrutura física cada um roda. A pendência estava registrada em `.claude/rules/alfaia-stack-deploy.md` e bloqueava as stories do Épico 9 (Operação). Resolvida nesta emenda — ver §24.2. Detalhamento operacional de Cloud Run em `docs/architecture/deploy-cloud-run-setup.md`.

### 24.1 Ambientes lógicos

| Ambiente | Uso | Banco |
|---|---|---|
| `local` | Desenvolvimento | Supabase local ou projeto dev |
| `producao` | Piloto e clientes | Projeto Supabase de produção |

Não há staging. Testes ocorrem em produção após deploy, com tenant de teste isolado.

### 24.2 Infraestrutura física por fase

| Fase | Infra de aplicação (Portal + Worker) | Banco | Motivo |
|---|---|---|---|
| Desenvolvimento e testes (fase atual) | **Cloud Run (GCP)** | Supabase | Iteração rápida, escala a zero, zero gestão de servidor durante o build do produto |
| Produção — pós-venda / operação com cliente real | **VPS: EasyPanel (Hostinger) ou Dockplot (Contabo)** | Supabase | Custo fixo previsível e controle total do host depois que o cliente fecha |

O Supabase **não migra** entre fases — é o mesmo projeto/banco do início ao fim. A escolha entre EasyPanel e Dockplot na fase de produção é **decisão comercial**, feita após cada venda — nenhuma story ou código assume qual dos dois será usado.

**Requisitos de portabilidade (não-negociáveis), para que a migração Cloud Run → VPS não exija reescrever nada:**

| # | Requisito |
|---|---|
| D1 | Portal e Worker possuem `Dockerfile` próprio — denominador comum entre Cloud Run e EasyPanel/Dockplot |
| D2 | Jobs agendados (§18.3: `debounce_worker`, `followup_scan`, `followup_expirar`, `agenda_sync`, `campanha_worker`, `transbordo_expirar`, `arquivar_ganhos`) são implementados como loop/cron **dentro do próprio Worker** — nunca amarrados a Cloud Scheduler, Cloud Tasks ou qualquer serviço proprietário do GCP sem equivalente rodável em VPS |
| D3 | Nenhum código hardcoda qual provedor de VPS será usado — variáveis de ambiente seguem o padrão de §24.4, sem acoplamento a EasyPanel ou Dockplot especificamente |
| D4 | No Cloud Run, o Worker precisa manter os loops de D2 vivos mesmo sem tráfego HTTP entrando — configuração obrigatória: `min-instances=1` + CPU sempre alocada (sem isso, os loops param quando a instância escala a zero). Esse comportamento equivale ao de uma VPS, que nunca escala a zero — **não é workaround temporário, é o modelo definitivo** |

### 24.3 Sequência de deploy (não negociável)

1. @dev implementa o código.
2. Se houver migration ou Edge Function, aplicar e confirmar sucesso **antes** de qualquer push.
3. Commit + push + PR **diretamente contra `main`**.
4. Revisão e validação do sócio.
5. Aprovação (ou pedido de correção).
6. Merge — já é produção.
7. Se o commit tocou `worker/`, redeploy manual no serviço de aplicação da fase vigente (Cloud Run hoje; EasyPanel ou Dockplot na fase de produção), pelo responsável designado.

Toda entrega deve declarar explicitamente se exige ajuste no Supabase e/ou redeploy, e em qual serviço.

### 24.4 Variáveis de ambiente

```
SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_ANON_KEY
WORKER_URL, WEBHOOK_INTERNAL_TOKEN, APP_URL
ANTHROPIC_API_KEY, OPENAI_API_KEY          # LLM e transcrição
WL_MODO=mock|real
UAZAPI_BASE_URL
AUCTAFLUX_BASE_URL, AUCTAFLUX_RESELLER_API_KEY
META_WEBHOOK_HMAC_ENFORCE=true|false
```

Nenhuma variável é específica de provedor de nuvem — o mesmo conjunto vale em Cloud Run e em qualquer VPS de produção.

---

## 25. Roadmap, épicos e stories

### 25.1 Fases

| Fase | Escopo | Prazo |
|---|---|---|
| **F0** Fundação | Supabase, multi-tenancy, RLS, portal base, auth | Semana 1 |
| **F1** Canal | Adapters, seletor, webhooks, idempotência | Semanas 2–3 |
| **F2** Identificação | `identificar_lead`, contexto, retomada, movimentação automática | Semana 4 |
| **F3** Atendimento | Motor com tools, debounce, transcrição, transbordo, painel | Semanas 5–6 |
| **F4** Integração WL | Camada anticorrupção (mock → real), produtos, slots, agendamento | Semana 7 |
| **F5** CRM | Kanban, timeline, follow-up, descarte | Semanas 8–9 |
| **F6** Base e campanhas | Contatos, segmentação, campanhas, opt-out | Semana 10 |
| **F7** Piloto | Loja piloto, ajuste de prompt, métricas | Semanas 11–13 |

F2 precede F3: o motor de IA depende do contexto de identificação para funcionar corretamente.

### 25.2 Stories

| Épico | ID | Story | Complexidade |
|---|---|---|---|
| **E1 Fundação** | S-01 | Schema base, enums e RLS | M |
| | S-02 | Auth, tenancy e RBAC | M |
| | S-03 | Shell do portal e navegação | S |
| **E2 Canal** | S-04 | Interface do adapter e capabilities | S |
| | S-05 | Adapter UAZAPI (envio + webhook) | M |
| | S-06 | Adapter Meta/AuctaFlux (envio + webhook + HMAC) | L |
| | S-07 | Idempotência e captura de webhook | S |
| | S-08 | Seletor de canal e bloqueio por janela de 24h | M |
| **E3 Identificação** | S-09 | Função `identificar_lead` e migration | M |
| | S-10 | Montagem do contexto do lead | M |
| | S-11 | Retomada e reengajamento na conversa | M |
| | S-12 | Histórico de interesse e detecção de mudança | M |
| | S-13 | Movimentação automática de status e regras MV1–MV6 | L |
| **E4 Atendimento** | S-14 | Debounce com SKIP LOCKED | M |
| | S-15 | Motor de IA e registro de tools | L |
| | S-16 | Transcrição de áudio | S |
| | S-17 | Painel de conversa realtime | M |
| | S-18 | Transbordo: assumir e devolver | M |
| **E5 Integração WL** | S-19 | Camada anticorrupção e mock | M |
| | S-20 | Consulta de produtos | M |
| | S-21 | Slots e criação de agendamento | M |
| | S-22 | Sync de agenda e tela por período | M |
| **E6 CRM** | S-23 | Kanban com drag-and-drop | M |
| | S-24 | Timeline do lead | S |
| | S-25 | Worker de follow-up | M |
| | S-26 | Disparo manual de follow-up | M |
| | S-27 | Descarte com retenção | S |
| **E7 Campanhas** | S-28 | Base de contatos e tags | M |
| | S-29 | Segmentação e prévia | M |
| | S-30 | Motor de campanha com K1–K8 | L |
| | S-31 | Opt-out e reversão | S |
| **E8 Configuração** | S-32 | Automações e toggles | S |
| | S-33 | Prompt, persona e parâmetros | M |
| | S-34 | Onboarding de tenant | M |
| **E9 Operação** | S-35 | Observabilidade e alertas | M |
| | S-36 | Exportação e exclusão LGPD | S |

---

## 26. Matriz de rastreabilidade

| Story | ACs cobertos | Seção |
|---|---|---|
| S-01, S-02 | RBAC §4.2, RLS §17.11, S1 | 4, 17, 22 |
| S-04–S-08 | AC 14.1–14.7 | 14 |
| S-09 | AC 9.1, 9.2, 9.5, T1, T2, T5, T6, T9 | 9 |
| S-10 | AC 9.3, 9.4 | 9 |
| S-11 | AC 9.4, AC 19.3, T3, T4 | 9, 19 |
| S-12 | AC 9.6, 9.7, T7, T8 | 9 |
| S-13 | AC 9.8–9.12, T10, T11 | 9 |
| S-14 | AC 8.4 | 8 |
| S-15 | AC 8.1, 8.2, 8.3, 8.7, AC 19.1, 19.2 | 8, 19 |
| S-16 | AC 8.5 | 8 |
| S-17 | AC 8.6, NFR9 | 8, 20 |
| S-18 | AC 13.1–13.5 | 13 |
| S-19–S-21 | AC 12.1–12.4, I1–I8 | 7, 12 |
| S-22 | AC 11.1–11.4 | 11 |
| S-23–S-27 | AC 10.1–10.7 | 10 |
| S-28–S-31 | AC 15.1–15.7, AC 9.13, 9.14, T12 | 9, 15 |
| S-32, S-33 | §16, §19 | 16, 19 |
| S-35 | §21 | 21 |
| S-36 | S8, S12 | 22 |

---

## 27. Definition of Ready / Done

### 27.1 Ready (a story pode entrar em desenvolvimento)

- [ ] Story referencia a seção do PRD que a fundamenta
- [ ] ACs em formato Given/When/Then, rastreáveis na matriz §26
- [ ] Nenhuma decisão de produto pendente dentro da story
- [ ] Migrations identificadas, se houver
- [ ] Dependências de outras stories declaradas
- [ ] Complexidade estimada (XS–XL)
- [ ] Executor e quality gate atribuídos
- [ ] Verificado que não viola nenhum item de §1.2

### 27.2 Done

- [ ] Todos os ACs verificados pelo @qa
- [ ] Testes da §23 aplicáveis passando
- [ ] Typecheck e lint zerados
- [ ] Migration aplicada e confirmada antes do push
- [ ] RLS verificada quando a story cria tabela
- [ ] File List e Change Log atualizados
- [ ] PR aberto contra `main`, revisado e aprovado
- [ ] Declarado explicitamente se exige ajuste no Supabase e/ou redeploy
- [ ] Nenhuma regressão nos fluxos existentes

---

## 28. Glossário

| Termo | Definição |
|---|---|
| **Contato** | Telefone único por tenant. Permanente. Pode ter vários leads ao longo do tempo |
| **Lead** | Uma intenção de negócio de um contato. Tem status, interesse e ciclo próprio |
| **`lead_seq`** | Número sequencial do lead dentro de um contato (1º, 2º, 3º) |
| **Continuação** | Retorno com lead ativo e silêncio menor que a janela |
| **Retomada** | Retorno com lead ativo e silêncio maior ou igual à janela |
| **Reengajamento** | Retorno de contato cujo último lead está fechado — gera lead novo |
| **Interesse** | Conjunto evento + data + peça + tamanho + cor + valor. Versionado |
| **Transbordo** | Passagem da conversa da IA para um humano |
| **Janela de 24h** | Restrição da Meta: texto livre só dentro de 24h da última mensagem do lead |
| **Capabilities** | Conjunto de restrições técnicas de um provider de canal |
| **Tenant** | Uma loja cliente do ALFAIA |
| **Descarte com retenção** | Lead sai do quadro visual mas permanece na base |

---

## 29. Questões abertas

| # | Questão | Responsável | Bloqueia |
|---|---|---|---|
| Q1 | Contrato exato dos endpoints da WebLocação (formato, auth, paginação, rate limit) | WebLocação | S-20, S-21 |
| Q2 | Os slots de agenda são por vaga ou horário fixo? Há capacidade simultânea? | WebLocação | S-21 |
| Q3 | O agendamento exige cliente já cadastrado no ERP, ou aceita nome + telefone? | WebLocação | S-21 |
| Q4 | O número do WhatsApp do piloto será novo ou o atual da loja? | Loja piloto | F7 |
| Q5 | Precificação: assinatura fixa, por volume, ou híbrido? | Optus Agent | — |
| Q6 | Comissão de indicação da WebLocação: recorrente ou única? | Optus Agent × WebLocação | — |
| Q7 | Janela de retomada de 7 dias se confirma na prática, ou o ciclo do setor pede mais? | Piloto | Ajuste de `ia_config` |
| Q8 | Qual modelo de LLM equilibra custo e qualidade dentro do NFR11? | Optus Agent | S-15 |

---

**Fim do documento.**

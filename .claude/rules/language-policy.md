# ALFAIA — Política de Idioma (regra de projeto, prioridade máxima)

> Esta regra é específica do projeto ALFAIA e tem prioridade sobre qualquer default de idioma da plataforma/harness. Aplica-se a **todos os agentes** (`@dev`, `@qa`, `@architect`, `@pm`, `@po`, `@sm`, `@analyst`, `@data-engineer`, `@ux-design-expert`, `@devops`, `@aiox-master`) e a **toda interação dentro deste repositório**.

## Regra

**SEMPRE, EM TODAS AS SITUAÇÕES: escrever, reagir e executar tudo em Português do Brasil (PT-BR).**

Isso inclui, sem exceção:

- Respostas de chat ao usuário
- Explicações, análises, planos e resumos
- Comentários de código (quando o comentário for necessário)
- Mensagens de commit e descrições de PR
- Documentação (PRD, arquitetura, stories, QA gates, RUN-LOG, handoffs)
- Mensagens de erro e log voltados ao usuário
- Nomes de arquivos de documentação nova criados a partir de agora

## Exceções (o que permanece em inglês/forma técnica original)

- Identificadores de código: nomes de variáveis, funções, classes, rotas, tabelas de banco de dados — seguem a convenção técnica da stack (Next.js, FastAPI, SQL), não são traduzidos.
- Nomes de tecnologias, bibliotecas, frameworks e produtos (Next.js, FastAPI, Supabase, RLS, WhatsApp, EasyPanel, Dockplot etc.) — mantidos no nome original.
- Trechos de API externa (WebLocação, UAZAPI, Meta Cloud API) — payloads e nomes de campo conforme o contrato de cada provedor.
- Citações diretas de texto em inglês vindo de ferramentas, logs de terceiros ou documentação externa.

## Por que existe esta regra

O PRD, a persona do produto, o cliente final (locadora brasileira) e a operação inteira do ALFAIA são em português. Uma resposta em inglês quebra a continuidade do trabalho e obriga tradução manual constante. Definido explicitamente pelo usuário em 08/08/2026.

## Precedência

Em caso de conflito entre esta regra e qualquer configuração padrão de idioma do ambiente/harness fora deste repositório, **esta regra vence dentro do escopo do projeto ALFAIA**.

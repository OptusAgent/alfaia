# wl-fake-api

> **⚠️ DADO SINTÉTICO.** Todo o catálogo servido por este serviço
> (`data/catalogo_sintetico.json`) foi **inventado para teste** — não é o
> catálogo real de nenhuma locadora cliente do ALFAIA. Se um dia os dados
> reais da WebLocação (ou de outro ERP) substituírem este mock, apague este
> aviso e o conteúdo de `data/` junto — não misture os dois.

## O que é

Um segundo mock, deliberado: um ERP fake **atrás de rede** (HTTP real, num
processo separado), implementando o contrato de `PRD §7.2` /
`docs/integracoes/weblocacao-solicitacao-api.md` — as mesmas rotas, os
mesmos nomes de campo.

Ele existe para fechar o `WL_MODO=real` do worker
(`worker/app/services/weblocacao_service.py`) sem depender do contrato real
da WebLocação, que ainda não foi confirmado (Q1–Q3 do PRD, ver o documento
de solicitação de acesso técnico). Apontando `WL_BASE_URL` para este
serviço, o caminho `WL_MODO=real` é exercitado de ponta a ponta: cliente
HTTP real, timeout de 8s, retry em 5xx, tradução da camada anticorrupção —
tudo o que o modo `WL_MODO=mock` (in-process, `WLMockAdapter`) não cobre
por rodar na mesma memória do worker.

**Não confundir com `WLMockAdapter`.** Os dois mocks coexistem por motivos
diferentes:

| | `WLMockAdapter` (`WL_MODO=mock`) | `wl-fake-api` (`WL_MODO=real` apontando pra cá) |
|---|---|---|
| Onde roda | In-process, dentro do worker | Processo HTTP separado |
| Serve para | Desenvolvimento do dia a dia, sem dependência externa | Testar o cliente HTTP real: timeout, retry 5xx, parsing |
| Dado | 2 produtos fixos, hardcoded no Python | Catálogo de 9 peças, servido por rota, com estoque por tamanho |

## Contrato implementado

```
GET  /produtos?categoria=&tamanho=&cor=&estilo=&q=
GET  /produtos/{id}
GET  /agenda/slots?tipo=&data_inicio=&data_fim=
POST /agenda
GET  /agenda?data_inicio=&data_fim=
```

Cada peça do catálogo é "explodida" em uma linha por tamanho (SKU) — porque
`GET /produtos` retorna um `tamanho` singular por item, não uma lista de
tamanhos por peça. `id` é por SKU (ex. `wl_p101_38`); `codigo` é o modelo
(ex. `V-101`), repetido entre os tamanhos da mesma peça.

`status` é `disponivel`/`indisponivel` conforme o estoque daquele tamanho
específico. `GET /produtos/{id}` só promete `disponivel_em` quando
`status=disponivel` — nunca inventa disponibilidade para peça sem estoque.

Autenticação: aceita qualquer `Authorization: Bearer <token>` não vazio —
simula I1 (chave por tenant) sem impor um valor fixo de teste.

## Catálogo sintético (9 peças, PRD-coerente)

Gerado a partir das imagens em `docs/img/` — todas descritas visualmente
(nenhum campo comercial vem das imagens; é dado inventado plausível para o
segmento de locação de trajes de festa/casamento).

| Código | Categoria | Peça | Cor | Estoque total (varia por tamanho) |
|---|---|---|---|---|
| V-101 | casamento/noiva | Vestido Aurora Tomara-que-Caia | Off-White | 6 (tam. 44 zerado) |
| V-102 | casamento/noiva | Vestido Elise Sereia Ombro a Ombro | Marfim | 4 |
| T-201 | casamento/traje-masculino | Terno Marinho Slim 3 Peças | Azul Marinho | 8 |
| T-202 | casamento/traje-masculino | Terno Areia Rústico 3 Peças | Bege Areia | 4 (tam. 50 zerado) |
| T-203 | casamento/traje-masculino | Terno Linho Praia Champanhe | Bege Claro | 6 |
| T-204 | casamento/traje-masculino | Terno Marinho Clássico Social | Azul Marinho | 5 |
| F-301 | festa/madrinha | Vestido Noite Preto Plissado | Preto | 6 (tam. 42 zerado) |
| F-302 | festa/madrinha | Vestido Festa Laranja Costas Abertas | Laranja | 6 |
| F-303 | festa/madrinha | Vestido Esmeralda Um Ombro Só | Verde Esmeralda | 6 |

Fonte única de verdade: `data/catalogo_sintetico.json`. A migration
`supabase/migrations/20260819130100_s49_wl_mock_seed_catalogo_sintetico.sql`
é gerada a partir deste mesmo arquivo — não editar os dois separadamente.

Casos deliberados para os testes de disponibilidade: **três** SKUs com
estoque zerado num tamanho específico (V-101/44, T-202/50, F-301/42), para
exercitar o caminho "status indisponível" sem inventar disponibilidade.

## Rodando local

```bash
cd wl-fake-api
python3 -m uvicorn app.main:app --reload --port 8090
curl -H "Authorization: Bearer teste" http://127.0.0.1:8090/produtos
```

## Testes

```bash
cd wl-fake-api
python3 -m pytest tests/ -v
```

Os testes de fechamento do `WL_MODO=real` (subida da wl-fake-api como
subprocesso real, não in-process) estão em
`worker/tests/test_weblocacao_real_mode.py`.

## Deploy

Segue a mesma estratégia de `.claude/rules/alfaia-stack-deploy.md`:
`Dockerfile` próprio, compatível com Cloud Run (desenvolvimento) e VPS via
EasyPanel/Dockplot (produção). Não há job agendado neste serviço — é um
ERP fake sem jobs, apenas request/response. Ver `docs/framework/tech-stack.md`
para as variáveis de ambiente padrão do produto.

## Limitações conhecidas (documentadas, não corrigidas nesta entrega)

- **Persistência de `WL_MODO` por tenant.** `wl_integracao.modo`
  (migration `20260815000000_s19_wl_integracao.sql`) já existe no schema,
  mas `WebLocacaoService._obter_modo()` lê hoje a variável de ambiente
  `WL_MODO` global, e só cai no override por tenant (`configurar_modo_tenant`,
  em memória) se ele já tiver sido setado nesta mesma execução do processo —
  não é lido de `wl_integracao.modo` no banco. Fora do escopo desta story;
  fica registrado como dívida técnica conhecida para a story que fechar o
  onboarding multi-tenant de verdade.
- **Estado da wl-fake-api é em memória.** Agendamentos e vagas ocupadas
  vivem no processo do serviço, resetando a cada deploy/restart — aceitável
  para um ERP fake de teste, não para produção (que nunca vai rodar contra
  este serviço; o real será a WebLocação de verdade, quando o contrato
  fechar).
- **Upload das imagens ao Supabase Storage não foi executado automaticamente.**
  `scripts/upload_catalogo_wl_mock.py` está pronto (`--dry-run` validado),
  mas requer confirmação explícita antes de rodar contra o projeto Supabase
  real — não há Supabase de dev separado (ver
  `.claude/rules/alfaia-stack-deploy.md`). Enquanto não for executado,
  `foto_url` no seed aponta para `/static/catalogo/<arquivo>` (caminho
  local servido pela própria wl-fake-api), não para uma URL do Storage.

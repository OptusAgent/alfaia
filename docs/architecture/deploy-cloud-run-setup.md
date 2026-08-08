# Orientação passo a passo — Cloud Run (fase de desenvolvimento e testes)

> Escopo: ambiente `local`/dev-cloud do PRD §24, usando a conta GCP que o usuário já tem em mãos. Produção pós-venda migra para VPS (EasyPanel/Hostinger ou Dockplot/Contabo) — ver `.claude/rules/alfaia-stack-deploy.md`. **@devops (Gage) é o dono operacional do pipeline real** (CI/CD é exclusivo dele, `agent-authority.md`); este documento é a orientação de setup manual inicial para destravar o time agora.

## 0. Pré-requisitos já confirmados nesta sessão

- Conta GCP disponível.
- Supabase já ativo e acessível (projeto `irewoqkwywsapiiytdau`).
- Acesso à UAZAPI.
- Conta Cloudflare disponível (uso descrito no passo 7).
- **Sem VPS Hostinger/EasyPanel ainda** — não bloqueia esta fase.
- **Sem domínio próprio ainda** — ver nota importante no passo 6: isso **não bloqueia** os webhooks de canal.

## 1. Projeto e billing

```bash
gcloud auth login
gcloud projects create alfaia-dev --name="ALFAIA Dev"
gcloud config set project alfaia-dev
gcloud beta billing projects link alfaia-dev --billing-account=<BILLING_ACCOUNT_ID>
```

`<BILLING_ACCOUNT_ID>` você pega em `gcloud beta billing accounts list`.

## 2. Habilitar as APIs necessárias

```bash
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com
```

## 3. Secret Manager para credenciais (requisito S2 do PRD — nunca em texto puro)

```bash
printf '%s' "$SUPABASE_SERVICE_ROLE_KEY" | gcloud secrets create supabase-service-role-key --data-file=-
printf '%s' "$WEBHOOK_INTERNAL_TOKEN" | gcloud secrets create webhook-internal-token --data-file=-
```

Repita para cada segredo da lista de §24 do PRD (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, tokens de canal por tenant ficam no banco criptografado, não aqui — só os segredos de nível de aplicação vão no Secret Manager).

## 4. Dockerfile — obrigatório para Portal e Worker

Conforme `.claude/rules/alfaia-stack-deploy.md`, item 1: "Portal e Worker precisam de Dockerfile — é o denominador comum entre Cloud Run e EasyPanel/Dockplot." Um `Dockerfile` por serviço, na raiz de cada um (`portal/Dockerfile`, `worker/Dockerfile`), ainda não existem no repositório — são entregáveis das primeiras stories de cada stack (Portal: story 1.3; Worker: story 4.1, que já introduz o primeiro processo de longa duração).

## 5. Deploy do Worker (FastAPI) — atenção ao padrão de jobs contínuos

**Ponto de atenção arquitetural, não solucionável só com configuração:** o PRD (§18.3, e a regra de deploy) exige que `debounce_worker`, `followup_scan`, `campanha_worker` etc. rodem como **loop dentro do próprio worker**, não como Cloud Scheduler/Cloud Tasks (para serem portáveis para a VPS depois). Mas o Cloud Run é, por padrão, **request-driven e escala a zero** — um loop em background dentro do processo não continua rodando se não houver requisição chegando e a instância for desligada.

**Solução recomendada para a fase Cloud Run (padrão documentado do próprio Cloud Run para "background workers"):**

```bash
gcloud run deploy alfaia-worker \
  --source ./worker \
  --region southamerica-east1 \
  --min-instances=1 \
  --no-cpu-throttling \
  --set-secrets=SUPABASE_SERVICE_ROLE_KEY=supabase-service-role-key:latest,WEBHOOK_INTERNAL_TOKEN=webhook-internal-token:latest \
  --set-env-vars=SUPABASE_URL=https://irewoqkwywsapiiytdau.supabase.co,WL_MODO=mock
```

- `--min-instances=1`: mantém uma instância sempre viva — sem isso, os loops de `debounce_worker`/`campanha_worker` param quando a instância escala a zero.
- `--no-cpu-throttling`: permite que a CPU continue alocada mesmo fora do ciclo de uma requisição HTTP (necessário para o loop rodar em background).
- Efeito colateral aceito: o worker deixa de ser "escala a zero" (custo de ~1 instância 24/7). Isso é consistente com o que já vai acontecer na VPS depois — lá também não há scale-to-zero. Não é um workaround temporário, é o mesmo modelo final.
- `southamerica-east1` (São Paulo) — mesma região do projeto Supabase (`sa-east-1` na AWS, mas mantenha o worker na região GCP mais próxima do Brasil para latência; Supabase e Cloud Run não precisam estar no mesmo provedor).

## 6. Deploy do Portal (Next.js) — este pode escalar a zero normalmente

```bash
gcloud run deploy alfaia-portal \
  --source ./portal \
  --region southamerica-east1 \
  --allow-unauthenticated \
  --set-env-vars=NEXT_PUBLIC_SUPABASE_URL=https://irewoqkwywsapiiytdau.supabase.co,WORKER_URL=<url-do-worker-do-passo-5>
```

## Nota importante — o domínio ausente NÃO bloqueia os webhooks

Cada serviço do Cloud Run recebe automaticamente uma URL HTTPS pública `https://alfaia-worker-xxxxx-rj.a.run.app`. Isso é suficiente para:
- Configurar o webhook da UAZAPI (`POST /webhook/{token}`).
- Configurar o `forward_to_url` da AuctaFlux (quando as credenciais chegarem, story 2.4).

O usuário listou "não temos domínio próprio" como uma pendência — **para a fase de desenvolvimento/piloto ela não é um bloqueio real**, só se torna relevante quando o produto for para a VPS de produção com marca própria (ligado à decisão comercial pós-venda, fora do escopo técnico atual).

## 7. Cloudflare — uso nesta fase

O PRD e as regras do projeto não especificam um uso obrigatório do Cloudflare hoje (nenhuma story o referencia). Usos plausíveis com a conta que o usuário já tem, quando fizerem sentido:
- DNS e proxy quando o domínio próprio existir (fase VPS/produção).
- Cloudflare Turnstile como CAPTCHA no fluxo de onboarding do portal, se necessário (não especificado no PRD — não implementar sem confirmação).

Não há ação necessária no Cloudflare nesta fase — registrar aqui apenas para não perder o recurso disponível.

## 8. CI/CD real (fora do escopo deste guia manual)

Este documento cobre o **primeiro deploy manual**, suficiente para destravar as stories de infraestrutura (1.x em diante). Pipeline automatizado (build on push, deploy automático) é CI/CD — autoridade exclusiva do `@devops` (`agent-authority.md`). Acionar `@devops` quando o time estiver pronto para automatizar.

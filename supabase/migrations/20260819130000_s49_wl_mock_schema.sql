-- Story wl-fake-api: schema wl_mock — estado do ERP fake da WebLocação usado
-- para testar WL_MODO=real ponta a ponta (worker/app/services/weblocacao_service.py
-- e o serviço standalone wl-fake-api/). Isolado em schema próprio para nunca ser
-- confundido com as tabelas de domínio real do ALFAIA (public.*).
--
-- DADO SINTÉTICO — ver wl-fake-api/README.md. Catálogo importado do arquivo
-- wl-fake-api/data/catalogo_sintetico.json (migration seguinte).

create schema if not exists wl_mock;

create table if not exists wl_mock.produtos (
  id text primary key,
  codigo text not null unique,
  nome text not null,
  categoria text not null,
  cor text not null,
  estilo text,
  tecido text,
  valor_locacao numeric(10, 2) not null,
  arquivo_origem text not null,
  foto_url text,
  criado_em timestamptz not null default now()
);

create table if not exists wl_mock.produto_tamanhos (
  produto_id text not null references wl_mock.produtos(id) on delete cascade,
  tamanho text not null,
  estoque int not null default 0,
  primary key (produto_id, tamanho)
);

create table if not exists wl_mock.agenda_slots (
  id bigserial primary key,
  tipo text not null default 'prova',
  data date not null,
  hora time not null,
  vagas_totais int not null default 2,
  vagas_livres int not null default 2,
  unique (tipo, data, hora)
);

create table if not exists wl_mock.agendamentos (
  id text primary key,
  tipo text not null default 'prova',
  data date not null,
  hora time not null,
  cliente_nome text not null,
  cliente_telefone text,
  produto_id text references wl_mock.produtos(id) on delete set null,
  observacao text,
  status text not null default 'confirmado',
  origem text not null default 'automacao',
  criado_em timestamptz not null default now()
);

create index if not exists produto_tamanhos_produto_idx on wl_mock.produto_tamanhos(produto_id);
create index if not exists agenda_slots_data_idx on wl_mock.agenda_slots(data, hora);
create index if not exists agendamentos_data_idx on wl_mock.agendamentos(data, hora);

comment on schema wl_mock is
  'ERP fake da WebLocação (dado sintético) para testar WL_MODO=real. Não é dado real de locadora. Ver wl-fake-api/README.md.';

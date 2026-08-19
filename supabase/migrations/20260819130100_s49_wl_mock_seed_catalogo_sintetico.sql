-- Story wl-fake-api: seed do catalogo sintetico de wl_mock, gerado a partir de
-- wl-fake-api/data/catalogo_sintetico.json (fonte unica de verdade do dado de teste).
-- DADO SINTETICO -- nao e catalogo real de nenhuma locadora. Ver wl-fake-api/README.md.

insert into wl_mock.produtos (id, codigo, nome, categoria, cor, estilo, tecido, valor_locacao, arquivo_origem, foto_url)
values
  ('wl_p101', 'V-101', 'Vestido Aurora Tomara-que-Caia', 'casamento/noiva', 'Off-White', 'Princesa (A-line)', 'Cetim', 890.0, 'noiva001.jpg', '/static/catalogo/noiva001.jpg'),
  ('wl_p102', 'V-102', 'Vestido Elise Sereia Ombro a Ombro', 'casamento/noiva', 'Marfim', 'Sereia', 'Cetim acetinado', 1050.0, 'noiva002.jpg', '/static/catalogo/noiva002.jpg'),
  ('wl_p201', 'T-201', 'Terno Marinho Slim 3 Peças', 'casamento/traje-masculino', 'Azul Marinho', 'Slim, 3 peças', 'Tricoline (poliéster/viscose)', 420.0, '0002.jpeg', '/static/catalogo/0002.jpeg'),
  ('wl_p202', 'T-202', 'Terno Areia Rústico 3 Peças', 'casamento/traje-masculino', 'Bege Areia', 'Slim, 3 peças', 'Linho', 450.0, 'TERNOMASCULINO001.jpg', '/static/catalogo/TERNOMASCULINO001.jpg'),
  ('wl_p203', 'T-203', 'Terno Linho Praia Champanhe', 'casamento/traje-masculino', 'Bege Claro', 'Slim, 3 peças', 'Linho leve', 460.0, 'TERNOMASCULINO002.jpg', '/static/catalogo/TERNOMASCULINO002.jpg'),
  ('wl_p204', 'T-204', 'Terno Marinho Clássico Social', 'casamento/traje-masculino', 'Azul Marinho', 'Clássico, 3 peças', 'Lã fria (worsted)', 480.0, 'TERNOMASCULINO003.jpg', '/static/catalogo/TERNOMASCULINO003.jpg'),
  ('wl_p301', 'F-301', 'Vestido Noite Preto Plissado', 'festa/madrinha', 'Preto', 'Sereia, gola halter', 'Crepe plissado', 380.0, 'VESTIDO01.jpg', '/static/catalogo/VESTIDO01.jpg'),
  ('wl_p302', 'F-302', 'Vestido Festa Laranja Costas Abertas', 'festa/madrinha', 'Laranja', 'Fluido, gola halter', 'Chiffon', 350.0, 'VESTIDO02.jpg', '/static/catalogo/VESTIDO02.jpg'),
  ('wl_p303', 'F-303', 'Vestido Esmeralda Um Ombro Só', 'festa/madrinha', 'Verde Esmeralda', 'Assimétrico, um ombro só', 'Jersey', 360.0, 'VESTIDO03.jpg', '/static/catalogo/VESTIDO03.jpg')
on conflict (id) do nothing;

insert into wl_mock.produto_tamanhos (produto_id, tamanho, estoque)
values
  ('wl_p101', '36', 1),
  ('wl_p101', '38', 2),
  ('wl_p101', '40', 2),
  ('wl_p101', '42', 1),
  ('wl_p101', '44', 0),
  ('wl_p102', '36', 1),
  ('wl_p102', '38', 1),
  ('wl_p102', '40', 1),
  ('wl_p102', '42', 1),
  ('wl_p201', '46', 2),
  ('wl_p201', '48', 3),
  ('wl_p201', '50', 2),
  ('wl_p201', '52', 1),
  ('wl_p202', '46', 1),
  ('wl_p202', '48', 2),
  ('wl_p202', '50', 0),
  ('wl_p202', '52', 1),
  ('wl_p203', '46', 2),
  ('wl_p203', '48', 2),
  ('wl_p203', '50', 2),
  ('wl_p204', '46', 1),
  ('wl_p204', '48', 1),
  ('wl_p204', '50', 1),
  ('wl_p204', '52', 2),
  ('wl_p301', '36', 2),
  ('wl_p301', '38', 3),
  ('wl_p301', '40', 1),
  ('wl_p301', '42', 0),
  ('wl_p302', '36', 1),
  ('wl_p302', '38', 2),
  ('wl_p302', '40', 2),
  ('wl_p302', '42', 1),
  ('wl_p303', '40', 2),
  ('wl_p303', '42', 2),
  ('wl_p303', '44', 1),
  ('wl_p303', '46', 1)
on conflict (produto_id, tamanho) do update set estoque = excluded.estoque;


-- Story 1.2/1.3: item de nav "Campanhas" precisa de um gate de leitura.
-- §4.2 só restringe CRIAR/disparar campanha (dono apenas) -- visualizar a
-- tela/lista de campanhas não tem restrição no texto do PRD. Mesmo padrão
-- de inferência das 3 permissões de leitura anteriores.
insert into private.permissoes_papel (papel, recurso, acao, permitido, fonte_prd) values
('dono','campanha','read', true, 'Leitura de campanhas — sem restrição no PRD; só criar/disparar é restrito (dono)'),
('atendente','campanha','read', true, 'Leitura de campanhas — sem restrição no PRD'),
('operador','campanha','read', true, 'Leitura de campanhas — sem restrição no PRD');

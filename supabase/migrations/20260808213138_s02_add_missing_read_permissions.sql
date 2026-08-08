-- Story 1.2 (PRD S-02): 3 permissoes de leitura usadas em §18.2
-- (atendimento:read, agenda:read, produto:read) nao tinham linha propria em
-- §4.2 -- a matriz de §4.2 so lista capacidades COM alguma restricao de
-- papel; leitura de conversas/agenda/produtos nao e restrita por nenhum
-- texto do PRD (§11, §12, §18.1 nao mencionam bloqueio de papel). Inferido
-- como leitura livre aos 3 papeis, pelo mesmo padrao ja usado em "Ver
-- pipeline e leads" e "Ver base de contatos" (unicas linhas 100% ✅ da
-- matriz). Descoberto ao montar o menu do Portal (story 1.3) e faltar
-- identificador para os itens "Conversas" e "Agenda".

insert into private.permissoes_papel (papel, recurso, acao, permitido, fonte_prd) values
('dono','atendimento','read', true, 'Leitura de conversas — sem restrição no PRD (§18.2 GET /conversas/{id}/mensagens)'),
('atendente','atendimento','read', true, 'Leitura de conversas — sem restrição no PRD'),
('operador','atendimento','read', true, 'Leitura de conversas — sem restrição no PRD'),
('dono','agenda','read', true, 'Leitura de agenda — §11, sem restrição de papel'),
('atendente','agenda','read', true, 'Leitura de agenda — §11, sem restrição de papel'),
('operador','agenda','read', true, 'Leitura de agenda — §11, sem restrição de papel'),
('dono','produto','read', true, 'Leitura de produtos — §12, sem restrição de papel'),
('atendente','produto','read', true, 'Leitura de produtos — §12, sem restrição de papel'),
('operador','produto','read', true, 'Leitura de produtos — §12, sem restrição de papel');

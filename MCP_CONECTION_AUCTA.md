MCP — sua IA operando a API
O servidor MCP conecta o Claude Desktop, Cursor, Cline e qualquer assistente compatível com MCP à sua conta reseller — criar instâncias, conectar números, enviar mensagens e gerenciar templates por linguagem natural. Roda local na máquina do cliente (stdio); a chave nunca sai dali.

1. Pré-requisitos
• Node.js 18+ instalado na máquina.
• Uma API key (aflx_rsl_…) — gere em API Keys. Uma chave já controla todas as instâncias.
2. Configurar (Claude Desktop)
Cole no arquivo de configuração do Claude Desktop e troque a chave pela sua:

macOS
~/Library/Application Support/Claude/claude_desktop_config.json
Windows
%APPDATA%\Claude\claude_desktop_config.json
Copiar
{
  "mcpServers": {
    "auctaflux-reseller": {
      "command": "npx",
      "args": ["-y", "@auctaflux/reseller-mcp"],
      "env": {
        "AUCTAFLUX_RESELLER_API_KEY": "aflx_rsl_sua_chave_aqui"
      }
    }
  }
}
Reinicie o Claude Desktop — as ferramentas da AuctaFlux aparecem no painel. O mesmo bloco funciona em Cursor e Cline.

3. URL customizada (opcional)
Para apontar a um ambiente self-hosted ou de staging, adicione AUCTAFLUX_BASE_URL no env:

Copiar
"env": {
  "AUCTAFLUX_RESELLER_API_KEY": "aflx_rsl_...",
  "AUCTAFLUX_BASE_URL": "https://api-flux.aucta.tech"
}
Ferramentas disponíveis
24
list_instances	GET	Lista todas as instâncias
get_instance	GET	Detalhes de uma instância
create_instance	POST	Cria uma nova instância
update_instance	PATCH	Atualiza nome ou webhook
archive_instance	DELETE	Arquiva (soft-delete) uma instância
get_connection_status	GET	Status da conexão WhatsApp
create_connect_link	POST	Gera link de onboarding do cliente
register_connection	POST	Envia o PIN 2FA
disconnect_connection	DELETE	Desconecta sem arquivar
rotate_forward_secret	POST	Rotaciona o HMAC do webhook
send_text_message	POST	Envia mensagem de texto
send_template_message	POST	Envia template aprovado
send_media_message	POST	Envia imagem/áudio/vídeo/documento
send_interactive_message	POST	Botões/lista/CTA/carrossel
mark_message_as_read	POST	Marca mensagem como lida
delete_message	DELETE	Apaga uma mensagem enviada
list_templates	GET	Lista templates da WABA
create_template	POST	Submete template pra revisão da Meta
delete_template	DELETE	Remove todas as variantes de um template
get_business_profile	GET	Perfil do WhatsApp Business
update_business_profile	PATCH	Atualiza o perfil (sobre, e-mail…)
get_usage	GET	Instâncias ativas + mensagens no mês
sync_contacts	POST	Importa contatos da WhatsApp Business App (janela 24h)
sync_history	POST	Importa histórico de mensagens ~6 meses (janela 24h)
Pacote: @auctaflux/reseller-mcp
Instalado automaticamente via npx — nada pra baixar à mão.
Ver no npm
V1 é stdio (roda na máquina do cliente). Upload de mídia e CRUD de chaves ficam no console. Um servidor MCP hospedado (HTTP) pode vir no futuro.

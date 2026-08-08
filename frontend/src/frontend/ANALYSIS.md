# ALFAIA — Análise Técnica & Arquitetura Modular Frontend

## 1. Análise do Protótipo HTML (Lógica & Componentes Principais)

O protótipo HTML do **ALFAIA — Atendimento e CRM Conversacional** foi projetado para integrar a operação de lojas de locação de trajes ao ERP **WebLocação**. As suas principais áreas funcionais e lógicas são:

### A. Pipeline CRM (Kanban Board)
- **Lógica**: Gerenciamento visual do funil de vendas em 7 etapas (`novo`, `qualificando`, `orcamento`, `follow_up`, `negociando`, `agendado`, `ganho`).
- **Métricas & Ações**:
  - Drag-and-drop de cards entre colunas com atualização imediata de estado.
  - Indicadores Visuais: Leads quentes (ícone fogo) e leads frios/aguardando disparo.
  - Botão de Ação Direta no Card: "Disparar Follow-up" quando o card está na coluna `follow_up`.
  - Drawer Lateral do Lead: Detalhamento completo do histórico, linha do tempo da WebLocação, orçamentos, e ação de descarte seguro (remove o card do quadro mantendo a pessoa na base).
  - Modal de Disparo de Follow-up: Seleção interativa de 4 templates de mensagem com interpolação de variáveis.

### B. Atendimento WhatsApp (Simulador Interativo)
- **Lógica**: Simulação em tempo real do fluxo de mensagens entre Cliente (`cli`), IA (`ia`), Atendente Humano (`ag`) e Sistema ERP (`sys`).
- **Recursos Chave**:
  - 3 Cenários pré-configurados: (1) Lead novo com consulta de trajes e agendamento de prova; (2) Lead frio recuperado após follow-up; (3) Handoff/Transbordo por assunto crítico (avaria no vestido) com tomada e devolução de controle pelo atendente.
  - Cards de Produtos: Renderização de trajes (vestidos longos e ternos) em cards com ilustração vetorial inline e preços.
  - Painel de Traces WebLocação ERP: Exibição em tempo real das chamadas HTTP da API (GET `/produtos`, GET `/agenda/slots`, POST `/agenda`).

### C. Agenda de Provas de Traje
- **Lógica**: Visualização em grade semanal dos horários de prova e atendimento.
- **Diferencial**:
  - Distinção clara da origem (Agendado pela Automação WhatsApp vs Criado na Loja).
  - Filtros por período, tipo e origem com ação de Sincronização em tempo real com o ERP.

### D. Base de Contatos & Segmentação
- **Lógica**: Banco de contatos unificado com retenção de leads descartados para campanhas de remarketing.
- **Filtros**: Tipo de evento (Casamento, Formatura, 15 anos), Mês do evento e Status final.
- **Ação**: Criação de campanhas direcionadas respeitando a lista de opt-outs.

### E. Automações de IA
- **Lógica**: 7 rotinas automatizadas com chaves de liga/desliga por loja e métricas de desempenho.

### F. Canais WhatsApp & Provedores
- **Lógica**: Seletor dinâmico entre **Meta Cloud API (Oficial)** e **UAZAPI (Não oficial)**, com exibição do payload JSON do webhook normalizado.

---

## 2. Relação dos Elementos Visuais (Imagem JPG) com a Estrutura de Código

A imagem `.jpg` ("DAILY REPORT CONCEPT") fornece a identidade visual executiva, paleta de cores e hierarquia de componentes. A correspondência entre a imagem e o código React modular foi estabelecida da seguinte forma:

| Elemento da Imagem (.jpg) | Componente no Frontend React (`/src/frontend/`) | Função no ALFAIA CRM |
| :--- | :--- | :--- |
| **Sidebar Azul Marinho Dark** | `Sidebar.tsx` | Menu lateral fixo com logo, card da atendente ("Juliana Prado"), badges de notificação e indicador do canal ativo. |
| **User Avatar + Avaliação Stars** | `Sidebar.tsx` (`User Avatar Card`) | Perfil da atendente responsável pela operação da loja. |
| **Topo / Search Bar & Ícones** | `Header.tsx` | Barra superior com campo de busca global, indicador de sync WebLocação e ações do sistema. |
| **01. Ribbon Bookmark Cards (01 a 07)** | `KpiRibbons.tsx` | Cards verticais em estilo fita/marcador para as métricas dos 7 dias da semana e etapas do funil. |
| **02. Report Graph (Área/Linha)** | `ReportGraph.tsx` | Gráfico vetorial de área mostrando a evolução semanal de conversão de trajes. |
| **03. Comparison Report (Donut)** | `ComparisonChart.tsx` | Gráfico radial tipo Donut comparando a taxa de resolução por IA vs Atendimento Humano. |
| **Dashboard Consolidado** | `ExecutiveReportView.tsx` | Visão que reúne os 3 infográficos da imagem com dados reais do CRM. |

---

## 3. Arquitetura Modular de Componentes

Organização dos arquivos dentro da pasta `/src/frontend/`:

```
/src/frontend/
├── types/
│   └── index.ts                # Interfaces TypeScript unificadas
├── data/
│   └── mockData.ts             # Dados do protótipo ALFAIA + WebLocação
├── components/
│   ├── common/                 # Componentes genéricos de UI
│   │   ├── Badge.tsx           # Tags coloridas de status
│   │   ├── Toast.tsx           # Notificações estilo Toast
│   │   ├── Header.tsx          # Cabeçalho da aplicação
│   │   └── Sidebar.tsx         # Menu de navegação lateral
│   ├── dashboard/              # Infográficos inspirados na imagem JPG
│   │   ├── KpiRibbons.tsx      # Cards diários estilo Bookmark / Ribbon
│   │   ├── ReportGraph.tsx     # Gráfico de Área do funil
│   │   ├── ComparisonChart.tsx # Gráfico Donut comparativo
│   │   └── ExecutiveReportView.tsx # Painel consolidado executivo
│   ├── pipeline/               # Módulo Kanban CRM
│   │   ├── LeadCard.tsx        # Card de lead com drag and drop
│   │   ├── LeadDrawer.tsx      # Painel lateral do lead com timeline
│   │   ├── FollowUpModal.tsx   # Modal de templates de follow-up
│   │   └── PipelineView.tsx    # Quadro Kanban em 7 colunas
│   ├── chat/                   # Módulo Atendimento WhatsApp
│   │   ├── ThreadMessage.tsx   # Mensagens do chat (Cliente, IA, Humano, Sistema)
│   │   ├── ProductCard.tsx     # Card vetorial de vestido/terno com valor
│   │   ├── HandoffBanner.tsx   # Banner de transbordo e tomada de controle
│   │   ├── WebLocacionTraces.tsx # Log de chamadas à API WebLocação
│   │   └── ChatView.tsx        # Simulador completo de conversa
│   ├── agenda/                 # Módulo de Agendamentos
│   │   └── AgendaView.tsx      # Calendário de provas integrado à WebLocação
│   ├── contacts/               # Módulo Base de Contatos
│   │   └── ContactsView.tsx    # Tabela de contatos e construtor de campanhas
│   ├── automations/            # Módulo de Automações IA
│   │   └── AutomationsView.tsx # Chaves de ligar/desligar e métricas
│   └── channel/                # Módulo Canal WhatsApp
│       └── ChannelView.tsx     # Seletor Meta Cloud API vs UAZAPI e inspector JSON
└── AppFrontend.tsx             # Componente raiz da aplicação
```

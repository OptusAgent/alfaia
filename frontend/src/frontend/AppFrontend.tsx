import React, { useState } from 'react';
import { NavigationPage, Lead, ToastMessage } from './types';
import { INITIAL_LEADS, PROVIDERS } from './data/mockData';
import { Sidebar } from './components/common/Sidebar';
import { Header } from './components/common/Header';
import { Toast } from './components/common/Toast';
import { PipelineView } from './components/pipeline/PipelineView';
import { ChatView } from './components/chat/ChatView';
import { AgendaView } from './components/agenda/AgendaView';
import { ContactsView } from './components/contacts/ContactsView';
import { AutomationsView } from './components/automations/AutomationsView';
import { ChannelView } from './components/channel/ChannelView';
import { ExecutiveReportView } from './components/dashboard/ExecutiveReportView';

export const AppFrontend: React.FC = () => {
  const [activePage, setActivePage] = useState<NavigationPage>('crm');
  const [leads, setLeads] = useState<Lead[]>(INITIAL_LEADS);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [activeChannelKey, setActiveChannelKey] = useState<string>('meta');
  const [selectedScenarioForChat, setSelectedScenarioForChat] = useState<string | undefined>(undefined);
  const [toast, setToast] = useState<ToastMessage | null>(null);

  const activeProvider = PROVIDERS.find((p) => p.k === activeChannelKey) || PROVIDERS[0];

  const showToast = (title: string, subtitle?: string) => {
    setToast({ id: Math.random().toString(), title, subtitle });
    setTimeout(() => {
      setToast(null);
    }, 3400);
  };

  const handleOpenChatFromLead = (leadId: string) => {
    setSelectedScenarioForChat('c1');
    setActivePage('att');
  };

  const pageDetails = {
    crm: {
      title: 'Pipeline de Leads',
      subtitle: 'Todo lead que chega, do primeiro oi ao contrato assinado na WebLocação',
    },
    att: {
      title: 'Atendimento WhatsApp',
      subtitle: 'Conversas do WhatsApp em tempo real com transbordo e retomada por IA',
    },
    agenda: {
      title: 'Agenda de Provas',
      subtitle: 'Provas e atendimentos de trajes sincronizados com a WebLocação',
    },
    base: {
      title: 'Base de Contatos & CRM',
      subtitle: 'Quem já falou com a loja — histórico completo e segmentação para remarketing',
    },
    reports: {
      title: 'Relatórios Executive Concept',
      subtitle: 'Painel analítico comparativo com a identidade do protótipo visual',
    },
    auto: {
      title: 'Automações Inteligentes',
      subtitle: 'Sete rotinas ativas por loja com métricas e regras de segurança',
    },
    canal: {
      title: 'Canais de Comunicação',
      subtitle: 'Meta Cloud API oficial vs UAZAPI com seletor dinâmico e webhook normalizado',
    },
  };

  const currentMeta = pageDetails[activePage];

  // Filter leads based on header search query
  const filteredLeads = leads.filter(
    (l) =>
      l.n.toLowerCase().includes(searchQuery.toLowerCase()) ||
      l.t.toLowerCase().includes(searchQuery.toLowerCase()) ||
      l.ev.toLowerCase().includes(searchQuery.toLowerCase()) ||
      l.pc.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-[#F3F6F9] text-[#1F1B17] flex flex-col lg:flex-row">
      {/* Navigation Sidebar */}
      <Sidebar
        activePage={activePage}
        onNavigate={(page) => setActivePage(page)}
        activeChannelName={activeProvider.n}
        activeChannelPhone={activeProvider.phone}
      />

      {/* Main Content Workspace */}
      <main className="flex-1 flex flex-col min-w-0 min-h-screen">
        <Header
          title={currentMeta.title}
          subtitle={currentMeta.subtitle}
          searchQuery={searchQuery}
          onSearchChange={(q) => setSearchQuery(q)}
          onRefreshSync={() => showToast('Dados Atualizados', 'Sincronização com WebLocação ERP efetuada.')}
        />

        <div className="p-4 md:p-6 lg:p-8 flex-1 max-w-[1600px] w-full mx-auto">
          {activePage === 'crm' && (
            <PipelineView
              leads={filteredLeads}
              onUpdateLeads={(updated) => setLeads(updated)}
              onOpenChat={handleOpenChatFromLead}
              onShowToast={showToast}
            />
          )}

          {activePage === 'att' && (
            <ChatView
              initialScenarioId={selectedScenarioForChat}
              onShowToast={showToast}
            />
          )}

          {activePage === 'agenda' && <AgendaView onShowToast={showToast} />}

          {activePage === 'base' && <ContactsView onShowToast={showToast} />}

          {activePage === 'reports' && <ExecutiveReportView />}

          {activePage === 'auto' && <AutomationsView onShowToast={showToast} />}

          {activePage === 'canal' && (
            <ChannelView
              activeChannelKey={activeChannelKey}
              onSelectChannel={(key) => setActiveChannelKey(key)}
              onShowToast={showToast}
            />
          )}
        </div>
      </main>

      {/* Floating Toast Notification */}
      <Toast toast={toast} />
    </div>
  );
};

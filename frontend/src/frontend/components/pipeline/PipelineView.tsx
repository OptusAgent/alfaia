import React, { useState } from 'react';
import { Lead, LeadStatus, KanbanColumn } from '../../types';
import { KANBAN_COLUMNS } from '../../data/mockData';
import { LeadCard } from './LeadCard';
import { LeadDrawer } from './LeadDrawer';
import { FollowUpModal } from './FollowUpModal';
import { Users, Clock, Calendar, Contact } from 'lucide-react';

interface PipelineViewProps {
  leads: Lead[];
  onUpdateLeads: (leads: Lead[]) => void;
  onOpenChat: (leadId: string) => void;
  onShowToast: (title: string, subtitle?: string) => void;
}

export const PipelineView: React.FC<PipelineViewProps> = ({
  leads,
  onUpdateLeads,
  onOpenChat,
  onShowToast,
}) => {
  const [selectedLeadId, setSelectedLeadId] = useState<string | null>(null);
  const [followUpLeadId, setFollowUpLeadId] = useState<string | null>(null);
  const [draggedLeadId, setDraggedLeadId] = useState<string | null>(null);
  const [dragOverCol, setDragOverCol] = useState<LeadStatus | null>(null);

  const activeLeadsCount = leads.filter((l) => l.st !== 'ganho').length;
  const followUpCount = leads.filter((l) => l.st === 'follow_up').length;
  const scheduledCount = leads.filter((l) => l.st === 'agendado').length;

  const handleDragStart = (e: React.DragEvent, id: string) => {
    setDraggedLeadId(id);
    e.dataTransfer.setData('text/plain', id);
  };

  const handleDragOver = (e: React.DragEvent, colKey: LeadStatus) => {
    e.preventDefault();
    setDragOverCol(colKey);
  };

  const handleDragLeave = () => {
    setDragOverCol(null);
  };

  const handleDrop = (e: React.DragEvent, targetCol: LeadStatus) => {
    e.preventDefault();
    setDragOverCol(null);

    const id = draggedLeadId || e.dataTransfer.getData('text/plain');
    if (!id) return;

    const leadToMove = leads.find((l) => l.id === id);
    if (!leadToMove || leadToMove.st === targetCol) return;

    const prevColName = KANBAN_COLUMNS.find((c) => c.k === leadToMove.st)?.n || leadToMove.st;
    const targetColName = KANBAN_COLUMNS.find((c) => c.k === targetCol)?.n || targetCol;

    const updated = leads.map((l) => {
      if (l.id === id) {
        return {
          ...l,
          st: targetCol,
          cold: targetCol === 'follow_up' ? true : false,
        };
      }
      return l;
    });

    onUpdateLeads(updated);
    setDraggedLeadId(null);
    onShowToast('Card movido', `${leadToMove.n}: ${prevColName} → ${targetColName}`);
  };

  const handleDiscardLead = (id: string) => {
    const leadToDiscard = leads.find((l) => l.id === id);
    const updated = leads.filter((l) => l.id !== id);
    onUpdateLeads(updated);
    setSelectedLeadId(null);
    if (leadToDiscard) {
      onShowToast('Lead descartado', `${leadToDiscard.n} saiu do quadro e permanece na base de contatos.`);
    }
  };

  const handleSendFollowUp = (templateIndex: number) => {
    if (!followUpLeadId) return;

    const lead = leads.find((l) => l.id === followUpLeadId);
    if (!lead) return;

    const updated = leads.map((l) => {
      if (l.id === followUpLeadId) {
        return {
          ...l,
          st: 'negociando' as LeadStatus,
          fu: (l.fu || 0) + 1,
          cold: false,
          h: 'agora',
        };
      }
      return l;
    });

    onUpdateLeads(updated);
    setFollowUpLeadId(null);
    onShowToast('Follow-up enviado', `Mensagem enviada para ${lead.n}. Card movido para Negociando.`);
  };

  const selectedLead = leads.find((l) => l.id === selectedLeadId) || null;
  const followUpLead = leads.find((l) => l.id === followUpLeadId) || null;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top KPIs matching ALFAIA Prototype */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-2xs relative overflow-hidden">
          <span className="font-mono text-[10px] uppercase tracking-wider text-slate-400 font-bold block">
            Leads Ativos
          </span>
          <div className="font-serif text-3xl font-medium text-slate-900 my-1">{activeLeadsCount}</div>
          <span className="text-xs text-slate-500">no quadro agora</span>
          <Users className="w-10 h-10 absolute right-3 bottom-3 text-slate-100 -z-0" />
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-2xs relative overflow-hidden">
          <span className="font-mono text-[10px] uppercase tracking-wider text-[#7B2233] font-bold block">
            Aguardando Follow-up
          </span>
          <div className="font-serif text-3xl font-medium text-[#7B2233] my-1">{followUpCount}</div>
          <span className="text-xs text-slate-500">botão de disparo ativo</span>
          <Clock className="w-10 h-10 absolute right-3 bottom-3 text-[#7B2233]/10 -z-0" />
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-2xs relative overflow-hidden">
          <span className="font-mono text-[10px] uppercase tracking-wider text-[#A67C2E] font-bold block">
            Provas Agendadas
          </span>
          <div className="font-serif text-3xl font-medium text-[#A67C2E] my-1">{scheduledCount}</div>
          <span className="text-xs text-slate-500">pela automação</span>
          <Calendar className="w-10 h-10 absolute right-3 bottom-3 text-[#A67C2E]/10 -z-0" />
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-2xs relative overflow-hidden">
          <span className="font-mono text-[10px] uppercase tracking-wider text-slate-400 font-bold block">
            Base de Contatos
          </span>
          <div className="font-serif text-3xl font-medium text-slate-900 my-1">1.284</div>
          <span className="text-xs text-slate-500">disponíveis para campanha</span>
          <Contact className="w-10 h-10 absolute right-3 bottom-3 text-slate-100 -z-0" />
        </div>
      </div>

      {/* Kanban Board Container */}
      <div className="overflow-x-auto pb-4">
        <div className="flex gap-3 min-w-[1240px]">
          {KANBAN_COLUMNS.map((col) => {
            const colLeads = leads.filter((l) => l.st === col.k);
            const isTarget = dragOverCol === col.k;

            return (
              <div
                key={col.k}
                onDragOver={(e) => handleDragOver(e, col.k)}
                onDragLeave={handleDragLeave}
                onDrop={(e) => handleDrop(e, col.k)}
                className={`flex-1 min-w-[210px] max-w-[240px] bg-[#FAF7F2] border rounded-2xl flex flex-col max-h-[660px] transition-colors ${
                  isTarget ? 'border-[#0E4A7B] bg-[#E2EDF8]' : 'border-slate-200/80'
                }`}
              >
                {/* Column Header */}
                <div className="p-3 border-b border-slate-200/80 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: col.c }}></span>
                    <b className="text-xs font-semibold text-slate-900">{col.n}</b>
                  </div>
                  <span className="font-mono text-[10px] bg-white border border-slate-200 text-slate-600 px-2 py-0.5 rounded-full font-bold">
                    {colLeads.length}
                  </span>
                </div>

                {/* Column Cards */}
                <div className="p-2 flex-1 overflow-y-auto space-y-2.5">
                  {colLeads.length === 0 ? (
                    <div className="h-24 border-2 border-dashed border-slate-200 rounded-xl grid place-items-center text-center p-2">
                      <span className="text-[11px] text-slate-400 italic">Nenhum lead nesta etapa</span>
                    </div>
                  ) : (
                    colLeads.map((lead) => (
                      <LeadCard
                        key={lead.id}
                        lead={lead}
                        onOpenLead={(id) => setSelectedLeadId(id)}
                        onTriggerFollowUp={(id) => setFollowUpLeadId(id)}
                        onDragStart={handleDragStart}
                        onDragEnd={() => {
                          setDraggedLeadId(null);
                          setDragOverCol(null);
                        }}
                      />
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <p className="font-mono text-[10px] text-slate-400 text-center tracking-wider uppercase">
        Arraste os cards entre colunas · clique no card para ver histórico completo · dados sincronizados com a WebLocação
      </p>

      {/* Drawer Overlay */}
      <LeadDrawer
        lead={selectedLead}
        columns={KANBAN_COLUMNS}
        onClose={() => setSelectedLeadId(null)}
        onOpenChat={onOpenChat}
        onTriggerFollowUp={(id) => setFollowUpLeadId(id)}
        onDiscardLead={handleDiscardLead}
      />

      {/* Follow Up Modal */}
      <FollowUpModal
        lead={followUpLead}
        onClose={() => setFollowUpLeadId(null)}
        onSend={handleSendFollowUp}
      />
    </div>
  );
};

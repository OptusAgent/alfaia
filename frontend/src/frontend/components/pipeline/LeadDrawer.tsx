import React from 'react';
import { Lead, KanbanColumn } from '../../types';
import { X, MessageSquare, Send, Trash2, Calendar, CheckCircle, Clock } from 'lucide-react';

interface LeadDrawerProps {
  lead: Lead | null;
  columns: KanbanColumn[];
  onClose: () => void;
  onOpenChat: (leadId: string) => void;
  onTriggerFollowUp: (leadId: string) => void;
  onDiscardLead: (leadId: string) => void;
}

export const LeadDrawer: React.FC<LeadDrawerProps> = ({
  lead,
  columns,
  onClose,
  onOpenChat,
  onTriggerFollowUp,
  onDiscardLead,
}) => {
  if (!lead) return null;

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .slice(0, 2)
      .join('');
  };

  const currentCol = columns.find((c) => c.k === lead.st);

  return (
    <div className="fixed inset-0 z-[100] flex justify-end">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-xs transition-opacity" onClick={onClose}></div>

      {/* Drawer Body */}
      <div className="relative w-full max-w-md bg-white h-full shadow-2xl border-l border-slate-200 flex flex-col z-10 animate-fade-in overflow-hidden">
        {/* Drawer Header */}
        <div className="p-5 border-b border-slate-100 flex items-center gap-3 bg-[#FAF7F2]">
          <div className="w-11 h-11 rounded-full bg-[#F2E7D0] text-[#A67C2E] font-bold text-base grid place-items-center flex-shrink-0">
            {getInitials(lead.n)}
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="font-serif text-xl font-medium text-slate-900 truncate">{lead.n}</h3>
            <p className="text-xs text-slate-500 font-mono">{lead.t} · {lead.or}</p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200/50 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Drawer Content Scroll */}
        <div className="flex-1 overflow-y-auto p-5 space-y-6">
          {/* Situation Fields */}
          <div className="space-y-2 pb-4 border-b border-slate-100 text-xs">
            <h4 className="font-mono text-[10px] uppercase tracking-widest text-slate-400 font-bold mb-3">
              Situação do Lead
            </h4>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Status no Funil</span>
              <span className="font-semibold" style={{ color: currentCol?.c || '#000' }}>
                {currentCol?.n || lead.st}
              </span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Evento e Data</span>
              <span className="font-semibold text-slate-800">{lead.ev}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Peça de Interesse</span>
              <span className="font-semibold text-slate-800">{lead.pc}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Valor Estimado</span>
              <span className="font-semibold text-emerald-700">{lead.v ? `R$ ${lead.v}` : '—'}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Origem</span>
              <span className="font-semibold text-slate-800">{lead.or}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Último Contato</span>
              <span className="font-semibold text-slate-800">há {lead.h}</span>
            </div>
            {lead.ag && (
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Prova Agendada</span>
                <span className="font-semibold text-[#A67C2E] flex items-center gap-1">
                  <Calendar className="w-3 h-3" /> {lead.ag}
                </span>
              </div>
            )}
            {lead.fu && (
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Follow-ups Enviados</span>
                <span className="font-semibold text-[#7B2233]">{lead.fu} de 3</span>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="space-y-3 pb-4 border-b border-slate-100">
            <h4 className="font-mono text-[10px] uppercase tracking-widest text-slate-400 font-bold">
              Ações Rápidas
            </h4>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => {
                  onClose();
                  onOpenChat(lead.id);
                }}
                className="bg-[#0E4A7B] text-white hover:bg-[#072F53] px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-xs"
              >
                <MessageSquare className="w-3.5 h-3.5" /> Abrir Conversa
              </button>

              {lead.st === 'follow_up' && (
                <button
                  onClick={() => onTriggerFollowUp(lead.id)}
                  className="bg-[#7B2233] text-white hover:bg-[#5E1A27] px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-xs"
                >
                  <Send className="w-3.5 h-3.5" /> Disparar Follow-up
                </button>
              )}

              <button
                onClick={() => onDiscardLead(lead.id)}
                className="bg-slate-100 text-slate-700 hover:bg-rose-50 hover:text-rose-700 px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" /> Descartar Lead
              </button>
            </div>
            <p className="text-[11px] text-slate-400 leading-normal">
              Ao descartar, o card sai do quadro Kanban, mas o contato permanece salvo na base com as tags apuradas para campanhas de remarketing.
            </p>
          </div>

          {/* Timeline History */}
          <div className="space-y-3">
            <h4 className="font-mono text-[10px] uppercase tracking-widest text-slate-400 font-bold">
              Linha do Tempo
            </h4>
            <div className="relative pl-5 space-y-4 border-l-2 border-slate-100">
              {lead.ag && (
                <div className="relative text-xs">
                  <span className="absolute -left-[25px] top-0 w-3 h-3 rounded-full bg-[#4B7A5B] border-2 border-white"></span>
                  <b className="block text-slate-800 font-semibold">Prova Agendada WebLocação</b>
                  <p className="text-slate-500 text-[11px] mt-0.5">{lead.ag} · gravada na WebLocação pela automação</p>
                  <span className="text-[10px] font-mono text-slate-400 block mt-1">há {lead.h}</span>
                </div>
              )}

              {lead.fu && (
                <div className="relative text-xs">
                  <span className="absolute -left-[25px] top-0 w-3 h-3 rounded-full bg-[#7B2233] border-2 border-white"></span>
                  <b className="block text-slate-800 font-semibold">Follow-up Enviado ({lead.fu}ª tentativa)</b>
                  <p className="text-slate-500 text-[11px] mt-0.5">Mensagem “Retomada leve” sem resposta imediata</p>
                  <span className="text-[10px] font-mono text-slate-400 block mt-1">há 1 dia</span>
                </div>
              )}

              {lead.v > 0 && (
                <div className="relative text-xs">
                  <span className="absolute -left-[25px] top-0 w-3 h-3 rounded-full bg-[#A67C2E] border-2 border-white"></span>
                  <b className="block text-slate-800 font-semibold">Orçamento Apresentado</b>
                  <p className="text-slate-500 text-[11px] mt-0.5">{lead.pc} · R$ {lead.v}</p>
                  <span className="text-[10px] font-mono text-slate-400 block mt-1">há {lead.h}</span>
                </div>
              )}

              <div className="relative text-xs">
                <span className="absolute -left-[25px] top-0 w-3 h-3 rounded-full bg-[#0E4A7B] border-2 border-white"></span>
                <b className="block text-slate-800 font-semibold">Lead Qualificado pela IA</b>
                <p className="text-slate-500 text-[11px] mt-0.5">{lead.ev !== '—' ? lead.ev : 'Iniciando qualificação'}</p>
                <span className="text-[10px] font-mono text-slate-400 block mt-1">há {lead.h}</span>
              </div>

              <div className="relative text-xs">
                <span className="absolute -left-[25px] top-0 w-3 h-3 rounded-full bg-slate-300 border-2 border-white"></span>
                <b className="block text-slate-800 font-semibold">Primeiro Contato WhatsApp</b>
                <p className="text-slate-500 text-[11px] mt-0.5">Entrou via {lead.or}</p>
                <span className="text-[10px] font-mono text-slate-400 block mt-1">há {lead.h}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

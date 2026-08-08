import React, { useState } from 'react';
import { Lead, FollowUpTemplate } from '../../types';
import { FOLLOW_UP_TEMPLATES } from '../../data/mockData';
import { X, Send, Check } from 'lucide-react';

interface FollowUpModalProps {
  lead: Lead | null;
  onClose: () => void;
  onSend: (templateIndex: number) => void;
}

export const FollowUpModal: React.FC<FollowUpModalProps> = ({ lead, onClose, onSend }) => {
  const [selectedIndex, setSelectedIndex] = useState<number>(0);

  if (!lead) return null;

  const leadFirstName = lead.n.split(' ')[0];
  const leadEvent = lead.ev.split(' · ')[0].toLowerCase();

  const getInterpolatedMessage = (template: FollowUpTemplate) => {
    return template.c
      .replace('{{nome}}', leadFirstName)
      .replace('{{evento}}', leadEvent || 'evento');
  };

  return (
    <div className="fixed inset-0 z-[110] flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs animate-fade-in">
      <div className="bg-white rounded-2xl w-full max-w-md shadow-2xl border border-slate-200 overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between bg-[#FAF7F2]">
          <h3 className="font-serif text-lg font-semibold text-slate-900">Disparar Follow-up WhatsApp</h3>
          <button onClick={onClose} className="p-1 text-slate-400 hover:text-slate-600 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          <p className="text-xs text-slate-600">
            Para <b className="text-slate-900">{lead.n}</b> ({lead.t}) · escolha a mensagem que será enviada pelo canal ativo.
          </p>

          <div className="space-y-2.5">
            {FOLLOW_UP_TEMPLATES.map((tmpl, idx) => {
              const isSelected = selectedIndex === idx;
              return (
                <div
                  key={idx}
                  onClick={() => setSelectedIndex(idx)}
                  className={`p-3 rounded-xl border text-xs cursor-pointer transition-all relative ${
                    isSelected
                      ? 'border-[#0E4A7B] bg-[#E2EDF8] shadow-xs'
                      : 'border-slate-200 hover:border-[#0E4A7B]/50 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <b className="font-semibold text-slate-900">{tmpl.n}</b>
                    {isSelected && <Check className="w-4 h-4 text-[#0E4A7B]" />}
                  </div>
                  <p className="text-slate-600 leading-relaxed">{getInterpolatedMessage(tmpl)}</p>
                </div>
              );
            })}
          </div>

          <button
            onClick={() => onSend(selectedIndex)}
            className="w-full mt-2 bg-[#0E4A7B] hover:bg-[#072F53] text-white py-2.5 rounded-xl font-semibold text-xs flex items-center justify-center gap-2 shadow-sm transition-all"
          >
            <Send className="w-4 h-4" /> Enviar Mensagem Agora
          </button>
        </div>
      </div>
    </div>
  );
};

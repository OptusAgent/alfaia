import React, { useState } from 'react';
import { AutomationRoutine } from '../../types';
import { AUTOMATIONS } from '../../data/mockData';
import { MessageSquare, Search, Calendar, Clock, Trash2, UserCheck, Send } from 'lucide-react';

interface AutomationsViewProps {
  onShowToast: (title: string, subtitle?: string) => void;
}

export const AutomationsView: React.FC<AutomationsViewProps> = ({ onShowToast }) => {
  const [routines, setRoutines] = useState<AutomationRoutine[]>(AUTOMATIONS);

  const getIcon = (type: string) => {
    switch (type) {
      case 'chat':
        return <MessageSquare className="w-4 h-4 text-[#A67C2E]" />;
      case 'search':
        return <Search className="w-4 h-4 text-[#A67C2E]" />;
      case 'calendar':
        return <Calendar className="w-4 h-4 text-[#A67C2E]" />;
      case 'clock':
        return <Clock className="w-4 h-4 text-[#A67C2E]" />;
      case 'trash':
        return <Trash2 className="w-4 h-4 text-[#A67C2E]" />;
      case 'userCheck':
        return <UserCheck className="w-4 h-4 text-[#A67C2E]" />;
      default:
        return <Send className="w-4 h-4 text-[#A67C2E]" />;
    }
  };

  const toggleRoutine = (index: number) => {
    const updated = [...routines];
    updated[index].on = !updated[index].on;
    setRoutines(updated);

    const statusStr = updated[index].on ? 'Automação Ativada' : 'Automação Pausada';
    onShowToast(statusStr, updated[index].n);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Grid of Automation Routines */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {routines.map((item, idx) => (
          <div
            key={idx}
            className={`bg-white border rounded-2xl p-4 shadow-2xs transition-all ${
              item.on ? 'border-slate-200' : 'border-slate-200/50 opacity-60'
            }`}
          >
            <div className="flex items-start justify-between gap-3 mb-3">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-[#F2E7D0] text-[#A67C2E] grid place-items-center flex-shrink-0">
                  {getIcon(item.ic)}
                </div>
                <div>
                  <b className="block text-xs font-semibold text-slate-900 leading-snug">{item.n}</b>
                  <span className="font-mono text-[9px] uppercase tracking-wider text-slate-400 block">
                    Gatilho: {item.g}
                  </span>
                </div>
              </div>

              {/* Toggle Switch */}
              <button
                onClick={() => toggleRoutine(idx)}
                className={`w-10 h-5 rounded-full p-0.5 transition-colors relative flex-shrink-0 ${
                  item.on ? 'bg-[#4B7A5B]' : 'bg-slate-300'
                }`}
              >
                <span
                  className={`w-4 h-4 rounded-full bg-white shadow-md block transition-transform ${
                    item.on ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed mb-4">{item.d}</p>

            <div className="flex items-center gap-4 pt-3 border-t border-slate-100 text-xs">
              {item.m.map((metric, mIdx) => (
                <div key={mIdx}>
                  <span className="font-mono text-[9px] uppercase tracking-wider text-slate-400 block">
                    {metric[0]}
                  </span>
                  <b className="font-serif text-base text-slate-900">{metric[1]}</b>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <p className="font-mono text-[10px] text-slate-400 text-center tracking-wider uppercase">
        Cada rotina liga e desliga por loja · segurança garantida: nenhuma automação escreve em contratos sem validação do operador
      </p>
    </div>
  );
};

import React, { useState } from 'react';
import { WEEKLY_SCHEDULE } from '../../data/mockData';
import { Info, RefreshCw, Calendar as CalendarIcon, UserCheck } from 'lucide-react';

interface AgendaViewProps {
  onShowToast: (title: string, subtitle?: string) => void;
}

export const AgendaView: React.FC<AgendaViewProps> = ({ onShowToast }) => {
  const [lastSyncTime, setLastSyncTime] = useState<string>('Último sync há 3 minutos');

  const handleSync = () => {
    setLastSyncTime('Último sync agora mesmo');
    onShowToast('Agenda Sincronizada', 'Dados atualizados a partir da WebLocação ERP.');
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Information Banner */}
      <div className="bg-[#E5EDF3] border border-[#4A6B84]/20 text-[#1F1B17] p-4 rounded-2xl flex items-start gap-3 text-xs leading-relaxed shadow-2xs">
        <Info className="w-5 h-5 text-[#4A6B84] flex-shrink-0 mt-0.5" />
        <div>
          <b>Sincronização Bidirecional WebLocação:</b> Esta tela reflete as provas e agendamentos gravados diretamente pela automação ou pelo portal da loja. Criações e cancelamentos manuais são feitos no ERP.
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-white border border-slate-200 rounded-2xl p-4 flex flex-wrap items-end justify-between gap-4 shadow-2xs">
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <div>
            <label className="font-mono text-[10px] uppercase tracking-wider text-slate-400 font-bold block mb-1">
              Período
            </label>
            <select className="bg-white border border-slate-200 rounded-xl px-3 py-1.5 text-xs focus:outline-none focus:border-[#0E4A7B]">
              <option>Semana atual</option>
              <option>Próxima semana</option>
              <option>Mês atual</option>
            </select>
          </div>

          <div>
            <label className="font-mono text-[10px] uppercase tracking-wider text-slate-400 font-bold block mb-1">
              Tipo
            </label>
            <select className="bg-white border border-slate-200 rounded-xl px-3 py-1.5 text-xs focus:outline-none focus:border-[#0E4A7B]">
              <option>Todos</option>
              <option>Prova de Traje</option>
              <option>Atendimento Loja</option>
            </select>
          </div>

          <div>
            <label className="font-mono text-[10px] uppercase tracking-wider text-slate-400 font-bold block mb-1">
              Origem
            </label>
            <select className="bg-white border border-slate-200 rounded-xl px-3 py-1.5 text-xs focus:outline-none focus:border-[#0E4A7B]">
              <option>Todas</option>
              <option>Automação WhatsApp</option>
              <option>Atendente Loja</option>
            </select>
          </div>

          <button
            onClick={handleSync}
            className="mt-4 bg-[#0E4A7B] hover:bg-[#072F53] text-white px-3.5 py-1.5 rounded-xl font-semibold text-xs flex items-center gap-1.5 shadow-2xs transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Sincronizar Agora
          </button>
        </div>

        <span className="font-mono text-xs text-slate-400">{lastSyncTime}</span>
      </div>

      {/* Weekly Schedule Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3">
        {WEEKLY_SCHEDULE.map((day, idx) => {
          const isToday = idx === 4; // Friday in sample
          return (
            <div
              key={idx}
              className={`bg-white border rounded-2xl overflow-hidden min-h-[220px] shadow-2xs ${
                isToday ? 'border-[#A67C2E]' : 'border-slate-200'
              }`}
            >
              {/* Day Header */}
              <div className={`p-2.5 border-b ${isToday ? 'bg-[#F2E7D0] border-[#A67C2E]/30' : 'bg-[#FAF7F2] border-slate-100'}`}>
                <b className="text-xs font-semibold text-slate-900">{day.d}</b>
                <small className="block font-mono text-[10px] text-slate-400">{day.n} AGO</small>
              </div>

              {/* Appointments List */}
              <div className="p-2 space-y-2">
                {day.i.map((slot, sIdx) => (
                  <div
                    key={sIdx}
                    className={`p-2 rounded-xl border text-xs border-l-4 ${
                      slot.k === 'at'
                        ? 'border-l-[#4A6B84] bg-[#E5EDF3] border-slate-200'
                        : 'border-l-[#A67C2E] bg-[#F2E7D0]/60 border-slate-200'
                    }`}
                  >
                    <span className="font-mono text-[10px] text-slate-500 block font-bold">{slot.t}</span>
                    <b className="block text-slate-900 font-semibold truncate">{slot.w}</b>
                    <span className="text-[10px] text-slate-600 block truncate">{slot.x}</span>
                    <span className="inline-block mt-1.5 font-mono text-[8px] uppercase tracking-wider px-1.5 py-0.2 rounded bg-white/80 font-bold text-slate-600">
                      {slot.b ? 'Automação' : 'Loja'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

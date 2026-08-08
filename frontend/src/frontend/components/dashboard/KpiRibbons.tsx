import React from 'react';
import { Calendar, TrendingUp, Sparkles, UserCheck, DollarSign } from 'lucide-react';

export const KpiRibbons: React.FC = () => {
  const days = [
    { num: '01', day: 'Domingo', val: 'R$ 1.280', label: 'Lead Novo', icon: <Sparkles className="w-3.5 h-3.5 text-amber-300" /> },
    { num: '02', day: 'Segunda', val: 'R$ 2.450', label: 'Qualificação', icon: <Calendar className="w-3.5 h-3.5 text-amber-300" /> },
    { num: '03', day: 'Terça', val: 'R$ 1.890', label: 'Orçamentos', icon: <DollarSign className="w-3.5 h-3.5 text-amber-300" /> },
    { num: '04', day: 'Quarta', val: 'R$ 3.120', label: 'Follow-ups', icon: <TrendingUp className="w-3.5 h-3.5 text-amber-300" /> },
    { num: '05', day: 'Quinta', val: 'R$ 2.760', label: 'Negociações', icon: <UserCheck className="w-3.5 h-3.5 text-amber-300" /> },
    { num: '06', day: 'Sexta', val: 'R$ 4.350', label: 'Provas Agendadas', icon: <Calendar className="w-3.5 h-3.5 text-amber-300" /> },
    { num: '07', day: 'Sábado', val: 'R$ 5.800', label: 'Contratos Ganhos', icon: <Sparkles className="w-3.5 h-3.5 text-amber-300" /> },
  ];

  return (
    <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm mb-6">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-100">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold text-[#0E4A7B] uppercase tracking-wider">01. Relatório Semanal</span>
            <span className="text-xs text-slate-400">· Período: Dia 01 - 07</span>
          </div>
          <h3 className="font-serif text-xl font-medium text-slate-800 mt-1">
            Métricas de Atendimento & Conversão de Leads
          </h3>
          <p className="text-xs text-slate-500 max-w-xl mt-0.5">
            Desempenho diário do funil conversacional ALFAIA com integração direta dos eventos e provas gravadas na WebLocação.
          </p>
        </div>

        <div className="bg-[#FAF7F2] p-3 rounded-xl border border-[#E7DFD2] flex items-center gap-4">
          <div>
            <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block">Total Geral Vendas</span>
            <span className="font-serif text-2xl font-bold text-[#A67C2E]">R$ 21.650</span>
          </div>
          <button className="bg-[#0E4A7B] text-white hover:bg-[#072F53] px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors shadow-xs">
            Mais detalhes
          </button>
        </div>
      </div>

      {/* 7 Vertical Ribbon Cards (Matching JPG Design) */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3 pt-2">
        {days.map((item) => (
          <div key={item.num} className="flex flex-col items-center text-center group">
            {/* Ribbon Card Container */}
            <div className="ribbon-card w-full py-4 px-2 text-white flex flex-col items-center justify-between min-h-[140px] relative">
              <div className="flex items-center justify-center gap-1">
                {item.icon}
                <span className="font-serif text-2xl font-bold text-[#EBB832]">{item.num}</span>
              </div>
              
              <p className="text-[10px] text-slate-200 line-clamp-2 px-1 leading-tight my-2">
                {item.label}
              </p>

              <div className="bg-white/15 backdrop-blur-xs px-2 py-0.5 rounded-full font-mono text-xs font-bold text-white border border-white/20">
                {item.val}
              </div>
            </div>

            {/* Bottom Label matching JPG Concept */}
            <div className="mt-3">
              <b className="block text-xs font-semibold text-[#0E4A7B]">{item.day}</b>
              <span className="text-[10px] text-slate-400 block mt-0.5">Conversão OK</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

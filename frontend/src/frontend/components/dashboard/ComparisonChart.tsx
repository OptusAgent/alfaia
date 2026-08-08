import React from 'react';

export const ComparisonChart: React.FC = () => {
  return (
    <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex flex-col justify-between h-full">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-xs font-bold text-[#0E4A7B] uppercase tracking-wider">
          03. Relatório Comparativo
        </span>
        <button className="text-slate-400 hover:text-slate-600 font-mono text-xs font-bold p-1">?</button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-center my-2">
        {/* Left Side Info */}
        <div className="space-y-3">
          <p className="text-xs text-slate-600 leading-relaxed">
            Comparativo de eficiência entre resolução automatizada por IA e atendimento humano especializado.
          </p>

          <div className="space-y-2 pt-2">
            <div className="flex items-center gap-3">
              <span className="w-3.5 h-7 rounded-full bg-[#0E4A7B]"></span>
              <div>
                <span className="text-[10px] font-mono text-slate-400 uppercase block">IA Automação (78%)</span>
                <b className="font-serif text-lg text-[#0E4A7B]">R$ 16.850</b>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span className="w-3.5 h-7 rounded-full bg-[#EBB832]"></span>
              <div>
                <span className="text-[10px] font-mono text-slate-400 uppercase block">Transbordo Humano (22%)</span>
                <b className="font-serif text-lg text-[#A67C2E]">R$ 4.800</b>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side Donut Graphic Matching JPG */}
        <div className="relative flex items-center justify-center py-2">
          <svg viewBox="0 0 160 160" className="w-36 h-36">
            {/* Outer Golden Circle Ring */}
            <circle
              cx="80"
              cy="80"
              r="62"
              fill="none"
              stroke="#EBB832"
              strokeWidth="14"
              strokeDasharray="390"
              strokeDashoffset="80"
              strokeLinecap="round"
            />
            {/* Inner Navy Circle Ring */}
            <circle
              cx="80"
              cy="80"
              r="46"
              fill="none"
              stroke="#0E4A7B"
              strokeWidth="12"
              strokeDasharray="290"
              strokeDashoffset="60"
              strokeLinecap="round"
            />
          </svg>

          {/* Center Badge matching JPG Concept */}
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-4">
            <span className="font-serif text-sm font-bold text-[#072F53] leading-tight">
              Automação
            </span>
            <span className="font-mono text-xs font-extrabold text-[#A67C2E] bg-[#F2E7D0] px-2 py-0.5 rounded-full mt-1">
              90% OK
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between text-[11px] text-slate-400 pt-3 border-t border-slate-100 font-mono">
        <span>Janeiro 2026 — ALFAIA CRM</span>
        <button className="text-[#0E4A7B] font-semibold hover:underline flex items-center gap-1">
          Próxima página &raquo;
        </button>
      </div>
    </div>
  );
};

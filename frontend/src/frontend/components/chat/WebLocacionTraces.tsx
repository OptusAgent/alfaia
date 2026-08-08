import React from 'react';

interface TraceItem {
  m: string; // Method
  p: string; // Path
  r: string; // Response
  w?: number; // Warning
}

interface WebLocacionTracesProps {
  contextFields: [string, string, string?][];
  traces: TraceItem[];
}

export const WebLocacionTraces: React.FC<WebLocacionTracesProps> = ({ contextFields, traces }) => {
  return (
    <div className="w-full lg:w-64 border-l border-slate-200 bg-[#FAF7F2] flex flex-col h-full text-xs">
      {/* Lead Context Panel */}
      <div className="p-4 border-b border-slate-200">
        <h4 className="font-mono text-[9px] uppercase tracking-widest text-slate-400 font-bold mb-3">
          Atributos do Lead
        </h4>
        <div className="space-y-2 text-xs">
          {contextFields.map(([label, val, key], idx) => (
            <div key={idx} className="flex justify-between items-center py-0.5">
              <span className="text-slate-500 text-[11px]">{label}</span>
              <span
                className={`font-semibold text-right truncate max-w-[120px] ${
                  val === '—' ? 'text-slate-400 font-normal italic' : 'text-slate-800'
                }`}
              >
                {val}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* WebLocação API Call Trace Inspector */}
      <div className="p-4 flex-1 flex flex-col min-h-0">
        <h4 className="font-mono text-[9px] uppercase tracking-widest text-slate-400 font-bold mb-3">
          Chamadas WebLocação ERP
        </h4>

        <div className="flex-1 overflow-y-auto space-y-2 pr-1">
          {traces.length === 0 ? (
            <div className="h-32 border border-dashed border-slate-200 rounded-xl grid place-items-center text-center p-2 text-slate-400 italic text-[11px]">
              Nenhuma chamada efetuada ainda.
            </div>
          ) : (
            traces.map((tr, idx) => (
              <div
                key={idx}
                className={`p-2 rounded-lg border text-[11px] font-mono leading-tight bg-white ${
                  tr.w ? 'border-l-4 border-l-[#A67C2E] border-slate-200' : 'border-l-4 border-l-[#4B7A5B] border-slate-200'
                }`}
              >
                <div className="flex items-center gap-1 font-bold text-[#0E4A7B]">
                  <span>{tr.m}</span>
                  <span className="text-slate-700 truncate">{tr.p}</span>
                </div>
                <div className="text-[#4B7A5B] mt-1 font-medium text-[10px]">↳ {tr.r}</div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

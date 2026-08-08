import React from 'react';

export const ReportGraph: React.FC = () => {
  // SVG Area Chart points matching the wave pattern in JPG
  const points = [
    { x: 30, y: 150, val: 210, label: 'Dia 01' },
    { x: 100, y: 120, val: 320, label: 'Dia 02' },
    { x: 170, y: 135, val: 280, label: 'Dia 03' },
    { x: 240, y: 90, val: 410, label: 'Dia 04' },
    { x: 310, y: 110, val: 350, label: 'Dia 05' },
    { x: 380, y: 70, val: 490, label: 'Dia 06' },
    { x: 450, y: 80, val: 460, label: 'Dia 07' },
  ];

  const svgPath = `M 30,150 Q 65,120 100,120 T 170,135 T 240,90 T 310,110 T 380,70 T 450,80 L 450,200 L 30,200 Z`;
  const linePath = `M 30,150 Q 65,120 100,120 T 170,135 T 240,90 T 310,110 T 380,70 T 450,80`;

  return (
    <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex flex-col justify-between h-full">
      <div className="flex items-center justify-between mb-4">
        <div>
          <span className="font-mono text-xs font-bold text-[#0E4A7B] uppercase tracking-wider block">
            02. Gráfico do Funil
          </span>
          <h4 className="font-serif text-lg font-medium text-slate-800">
            Evolução Semanal de Atendimentos
          </h4>
          <span className="text-xs text-slate-400">Período: Dia 01 - 07</span>
        </div>
        <button className="text-slate-400 hover:text-slate-600 font-mono text-xs font-bold p-1">?</button>
      </div>

      <div className="relative w-full overflow-hidden my-2">
        <svg viewBox="0 0 480 220" className="w-full h-auto">
          <defs>
            <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#0E4A7B" stopOpacity="0.75" />
              <stop offset="100%" stopColor="#0E4A7B" stopOpacity="0.05" />
            </linearGradient>
          </defs>

          {/* Grid Horizontal Lines */}
          <line x1="20" y1="50" x2="460" y2="50" stroke="#E2E8F0" strokeDasharray="3 3" />
          <line x1="20" y1="90" x2="460" y2="90" stroke="#E2E8F0" strokeDasharray="3 3" />
          <line x1="20" y1="130" x2="460" y2="130" stroke="#E2E8F0" strokeDasharray="3 3" />
          <line x1="20" y1="170" x2="460" y2="170" stroke="#E2E8F0" strokeDasharray="3 3" />
          <line x1="20" y1="200" x2="460" y2="200" stroke="#CBD5E1" strokeWidth="1" />

          {/* Filled Area */}
          <path d={svgPath} fill="url(#areaGradient)" />

          {/* Stroke Line */}
          <path d={linePath} fill="none" stroke="#0E4A7B" strokeWidth="3" strokeLinecap="round" />

          {/* Golden Data Dots matching JPG */}
          {points.map((pt, idx) => (
            <g key={idx}>
              <circle cx={pt.x} cy={pt.y} r="5" fill="#EBB832" stroke="#FFFFFF" strokeWidth="2" />
              <text x={pt.x} y={pt.y - 10} textAnchor="middle" fill="#0E4A7B" fontSize="9" fontWeight="bold">
                {pt.val}
              </text>
              <text x={pt.x} y={215} textAnchor="middle" fill="#94A3B8" fontSize="9" fontFamily="monospace">
                {pt.label}
              </text>
            </g>
          ))}
        </svg>
      </div>

      <div className="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-100 font-mono">
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-[#0E4A7B]"></span> Vendas
        </span>
        <span className="text-slate-400">* em número de trajes</span>
      </div>
    </div>
  );
};

import React from 'react';
import { KpiRibbons } from './KpiRibbons';
import { ReportGraph } from './ReportGraph';
import { ComparisonChart } from './ComparisonChart';
import { Sparkles, ArrowUpRight, ShieldCheck, Zap } from 'lucide-react';

export const ExecutiveReportView: React.FC = () => {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top Banner introducing the Executive Infographic layout inspired by JPG */}
      <div className="bg-gradient-to-r from-[#072F53] to-[#0E4A7B] text-white rounded-2xl p-6 shadow-md border border-[#1868A8]/30 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="bg-[#EBB832] text-[#072F53] font-mono text-[10px] font-bold px-2 py-0.5 rounded-full uppercase">
              Relatório Executivo
            </span>
            <span className="text-xs text-slate-200">Painel com Infográfico do Protótipo</span>
          </div>
          <h2 className="font-serif text-2xl md:text-3xl font-medium">
            Sintonia do CRM ALFAIA & Integração WebLocação
          </h2>
          <p className="text-xs text-slate-200 mt-1 max-w-2xl">
            Visão consolidada unindo a identidade visual do conceito executivo às funcionalidades do protótipo conversacional.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-white/10 backdrop-blur-md p-3 rounded-xl border border-white/20 text-center min-w-[120px]">
            <span className="text-[10px] text-slate-200 font-mono block">Sincronização</span>
            <b className="text-sm font-semibold text-[#EBB832] flex items-center justify-center gap-1 mt-0.5">
              <ShieldCheck className="w-3.5 h-3.5" /> 100% ERP
            </b>
          </div>
          <div className="bg-white/10 backdrop-blur-md p-3 rounded-xl border border-white/20 text-center min-w-[120px]">
            <span className="text-[10px] text-slate-200 font-mono block">Tempo Resposta</span>
            <b className="text-sm font-semibold text-emerald-300 flex items-center justify-center gap-1 mt-0.5">
              <Zap className="w-3.5 h-3.5" /> 180ms
            </b>
          </div>
        </div>
      </div>

      {/* 01. Ribbon Bookmark KPI Cards */}
      <KpiRibbons />

      {/* Grid for 02. Report Graph & 03. Comparison Report */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ReportGraph />
        <ComparisonChart />
      </div>
    </div>
  );
};

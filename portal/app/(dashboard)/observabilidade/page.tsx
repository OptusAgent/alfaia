"use client";

import { useState } from "react";
import { Activity, AlertTriangle, ShieldCheck, Terminal, Server, CheckCircle2, Clock, RefreshCw } from "lucide-react";

export default function ObservabilidadePage() {
  const [alertas, setAlertas] = useState<any[]>([
    {
      id: "alt_1",
      tipo: "campanha_pausada_k8",
      titulo: "Campanha Pausada por Falha | Regra K8 Acionada",
      mensagem: "K8 acionado: taxa de falha (17.6%) excedeu 15% em 51 disparos.",
      severidade: "critico",
      gerado_em: "2026-08-15T02:10:00.000Z",
    },
    {
      id: "alt_2",
      tipo: "integracao_wl_fora",
      titulo: "Integração WebLocação - Instabilidade Detectada",
      mensagem: "A API da WebLocação apresentou 3 falhas consecutivas (Timeout 8s).",
      severidade: "warning",
      gerado_em: "2026-08-15T01:45:00.000Z",
    },
  ]);

  const [logsSimulados, setLogsSimulados] = useState<any[]>([
    { timestamp: "02:14:01", etapa: "webhook_recebido", latencia_ms: 12, resultado: "200_OK", erro: null },
    { timestamp: "02:14:02", etapa: "identificacao_lead", latencia_ms: 45, resultado: "lead_reconhecido", erro: null },
    { timestamp: "02:14:03", etapa: "consulta_weblocacao", latencia_ms: 180, resultado: "sucesso", erro: null },
    { timestamp: "02:14:05", etapa: "llm_resposta_gerada", latencia_ms: 620, resultado: "sucesso", erro: null },
  ]);

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="border-b border-neutral-200 pb-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900 flex items-center gap-2.5">
            <Activity className="h-7 w-7 text-brand-600" />
            Central de Observabilidade & Alertas Operacionais
          </h1>
          <p className="text-sm text-neutral-500 mt-1">
            Monitoramento de logs estruturados em JSON e matriz de falhas críticas (PRD §21.1, §21.3).
          </p>
        </div>

        <button className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-neutral-300 text-xs font-semibold text-neutral-700 bg-white hover:bg-neutral-50">
          <RefreshCw className="h-3.5 w-3.5" /> Atualizar Telemetria
        </button>
      </div>

      {/* Grid de Status da Infraestrutura */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-neutral-200 shadow-2xs">
          <div className="text-xs text-neutral-500 font-semibold">Canal WhatsApp (UAZAPI)</div>
          <div className="text-sm font-bold text-emerald-700 flex items-center gap-1.5 mt-1">
            <CheckCircle2 className="h-4 w-4 text-emerald-600" /> Conectado (100%)
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-neutral-200 shadow-2xs">
          <div className="text-xs text-neutral-500 font-semibold">Qualidade do Número</div>
          <div className="text-sm font-bold text-emerald-700 flex items-center gap-1.5 mt-1">
            <ShieldCheck className="h-4 w-4 text-emerald-600" /> Alta (Verde)
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-neutral-200 shadow-2xs">
          <div className="text-xs text-neutral-500 font-semibold">ERP WebLocação</div>
          <div className="text-sm font-bold text-amber-700 flex items-center gap-1.5 mt-1">
            <Server className="h-4 w-4 text-amber-600" /> Modo Mock (Habilitado)
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-neutral-200 shadow-2xs">
          <div className="text-xs text-neutral-500 font-semibold">Latência Média LLM</div>
          <div className="text-sm font-bold text-neutral-900 flex items-center gap-1.5 mt-1">
            <Clock className="h-4 w-4 text-brand-600" /> 620 ms
          </div>
        </div>
      </div>

      {/* Seção 1: Central de Alertas Críticos (§21.3, AC 3) */}
      <div className="bg-white p-6 rounded-xl border border-neutral-200 shadow-2xs space-y-4">
        <h2 className="text-sm font-bold text-neutral-900 flex items-center gap-2 border-b pb-2">
          <AlertTriangle className="h-4 w-4 text-amber-600" /> Alertas Operacionais Ativos (6 Matrizes de Proteção)
        </h2>

        <div className="space-y-3">
          {alertas.map((alerta) => (
            <div
              key={alerta.id}
              className={`p-4 rounded-xl border flex items-start justify-between ${
                alerta.severidade === "critico"
                  ? "bg-red-50/70 border-red-200 text-red-950"
                  : "bg-amber-50/70 border-amber-200 text-amber-950"
              }`}
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-sm">{alerta.titulo}</span>
                  <span
                    className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                      alerta.severidade === "critico" ? "bg-red-200 text-red-900" : "bg-amber-200 text-amber-900"
                    }`}
                  >
                    {alerta.severidade}
                  </span>
                </div>
                <p className="text-xs">{alerta.mensagem}</p>
                <div className="text-[10px] text-neutral-500 font-mono mt-1">
                  Gerado em: {new Date(alerta.gerado_em).toLocaleTimeString("pt-BR")}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Seção 2: Stream de Logs JSON Estruturados (§21.1, AC 1) */}
      <div className="bg-neutral-950 text-neutral-100 p-6 rounded-xl space-y-3 font-mono text-xs shadow-md">
        <div className="flex items-center justify-between border-b border-neutral-800 pb-2">
          <span className="font-bold text-neutral-300 flex items-center gap-2">
            <Terminal className="h-4 w-4 text-brand-400" /> Stream de Logs JSON Estruturados (PRD §21.1)
          </span>
          <span className="text-[10px] text-emerald-400 font-bold bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-800">
            ● AO VIVO
          </span>
        </div>

        <div className="space-y-1.5 overflow-x-auto">
          {logsSimulados.map((log, idx) => (
            <div key={idx} className="text-neutral-300">
              <span className="text-neutral-500">[{log.timestamp}]</span>{" "}
              <span className="text-brand-300 font-bold">"{log.etapa}"</span> | latência:{" "}
              <span className="text-amber-300">{log.latencia_ms}ms</span> | resultado:{" "}
              <span className="text-emerald-400">{log.resultado}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

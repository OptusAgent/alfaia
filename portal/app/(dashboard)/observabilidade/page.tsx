"use client";

import { useState } from "react";
import { StatCard } from "@/app/components/ui/StatCard";
import {
  Activity,
  AlertTriangle,
  ShieldCheck,
  Terminal,
  Server,
  CheckCircle2,
  Clock,
  RefreshCw,
} from "lucide-react";

export default function ObservabilidadePage() {
  const [alertas] = useState<
    {
      id: string;
      tipo: string;
      titulo: string;
      mensagem: string;
      severidade: string;
      gerado_em: string;
    }[]
  >([
    {
      id: "alt_1",
      tipo: "campanha_pausada_k8",
      titulo: "Campanha Pausada por Falha | Regra K8 Acionada",
      mensagem:
        "K8 acionado: taxa de falha (17.6%) excedeu 15% em 51 disparos.",
      severidade: "critico",
      gerado_em: "2026-08-15T02:10:00.000Z",
    },
    {
      id: "alt_2",
      tipo: "integracao_wl_fora",
      titulo: "Integração WebLocação - Instabilidade Detectada",
      mensagem:
        "A API da WebLocação apresentou 3 falhas consecutivas (Timeout 8s).",
      severidade: "warning",
      gerado_em: "2026-08-15T01:45:00.000Z",
    },
  ]);

  const [logsSimulados] = useState([
    {
      timestamp: "02:14:01",
      etapa: "webhook_recebido",
      latencia_ms: 12,
      resultado: "200_OK",
      erro: null,
    },
    {
      timestamp: "02:14:02",
      etapa: "identificacao_lead",
      latencia_ms: 45,
      resultado: "lead_reconhecido",
      erro: null,
    },
    {
      timestamp: "02:14:03",
      etapa: "consulta_weblocacao",
      latencia_ms: 180,
      resultado: "sucesso",
      erro: null,
    },
    {
      timestamp: "02:14:05",
      etapa: "llm_resposta_gerada",
      latencia_ms: 620,
      resultado: "sucesso",
      erro: null,
    },
  ]);

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div
        className="flex items-center justify-between pb-4"
        style={{ borderBottom: "1px solid var(--line)" }}
      >
        <div>
          <h1
            className="text-2xl font-bold font-display flex items-center gap-2.5"
            style={{ color: "var(--text-primary)" }}
          >
            <Activity
              className="h-7 w-7"
              style={{ color: "var(--accent-primary)" }}
            />
            Observabilidade & Alertas
          </h1>
          <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
            Monitoramento de logs estruturados e matriz de falhas críticas.
          </p>
        </div>

        <button className="glass-btn glass-btn-ghost text-xs">
          <RefreshCw className="h-3.5 w-3.5" /> Atualizar Telemetria
        </button>
      </div>

      {/* Status Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <StatCard
          label="Canal WhatsApp"
          value="Conectado"
          icon={<CheckCircle2 className="h-4 w-4" />}
          trend={{ value: "100%", positive: true }}
        />
        <StatCard
          label="Qualidade do Número"
          value="Alta"
          icon={<ShieldCheck className="h-4 w-4" />}
          trend={{ value: "Verde", positive: true }}
        />
        <StatCard
          label="ERP WebLocação"
          value="Modo Mock"
          icon={
            <Server
              className="h-4 w-4"
              style={{ color: "var(--accent-amber)" }}
            />
          }
        />
        <StatCard
          label="Latência Média LLM"
          value="620 ms"
          icon={<Clock className="h-4 w-4" />}
        />
      </div>

      {/* Alerts */}
      <div className="glass-card p-6 space-y-4">
        <h2
          className="text-sm font-bold flex items-center gap-2 pb-2"
          style={{
            color: "var(--text-primary)",
            borderBottom: "1px solid var(--line)",
          }}
        >
          <AlertTriangle
            className="h-4 w-4"
            style={{ color: "var(--accent-amber)" }}
          />
          Alertas Operacionais Ativos
        </h2>

        <div className="space-y-3">
          {alertas.map((alerta) => (
            <div
              key={alerta.id}
              className="p-4 rounded-xl flex items-start justify-between"
              style={{
                background:
                  alerta.severidade === "critico"
                    ? "var(--accent-coral-muted)"
                    : "var(--accent-amber-muted)",
                border:
                  alerta.severidade === "critico"
                    ? "1px solid rgba(232, 76, 94, 0.2)"
                    : "1px solid var(--accent-amber-border)",
              }}
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span
                    className="font-bold text-sm"
                    style={{ color: "var(--text-primary)" }}
                  >
                    {alerta.titulo}
                  </span>
                  <span
                    className="text-[10px] font-extrabold px-2 py-0.5 rounded-full uppercase tracking-wider"
                    style={{
                      background:
                        alerta.severidade === "critico"
                          ? "rgba(232, 76, 94, 0.2)"
                          : "rgba(245, 158, 11, 0.2)",
                      color:
                        alerta.severidade === "critico"
                          ? "var(--accent-coral)"
                          : "var(--accent-amber)",
                    }}
                  >
                    {alerta.severidade}
                  </span>
                </div>
                <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                  {alerta.mensagem}
                </p>
                <div
                  className="text-[10px] font-mono mt-1"
                  style={{ color: "var(--text-muted)" }}
                >
                  Gerado em:{" "}
                  {new Date(alerta.gerado_em).toLocaleTimeString("pt-BR")}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Log Stream */}
      <div
        className="p-6 rounded-xl space-y-3 font-mono text-xs"
        style={{
          background: "#08090D",
          border: "1px solid var(--line)",
        }}
      >
        <div
          className="flex items-center justify-between pb-2"
          style={{ borderBottom: "1px solid var(--line)" }}
        >
          <span
            className="font-bold flex items-center gap-2"
            style={{ color: "var(--text-muted)" }}
          >
            <Terminal
              className="h-4 w-4"
              style={{ color: "var(--accent-primary)" }}
            />
            Stream de Logs JSON Estruturados
          </span>
          <span
            className="text-[10px] font-bold px-2 py-0.5 rounded"
            style={{
              background: "var(--accent-primary-muted)",
              color: "var(--accent-primary)",
              border: "1px solid rgba(16, 185, 129, 0.2)",
            }}
          >
            ● AO VIVO
          </span>
        </div>

        <div className="space-y-1.5 overflow-x-auto">
          {logsSimulados.map((log, idx) => (
            <div key={idx} style={{ color: "var(--text-muted)" }}>
              <span style={{ color: "var(--text-muted)" }}>
                [{log.timestamp}]
              </span>{" "}
              <span
                className="font-bold"
                style={{ color: "var(--accent-primary)" }}
              >
                &quot;{log.etapa}&quot;
              </span>{" "}
              | latência:{" "}
              <span style={{ color: "var(--accent-amber)" }}>
                {log.latencia_ms}ms
              </span>{" "}
              | resultado:{" "}
              <span style={{ color: "var(--accent-primary)" }}>
                {log.resultado}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

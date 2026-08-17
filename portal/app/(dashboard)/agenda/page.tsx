"use client";

import { useState } from "react";
import Link from "next/link";
import { Badge } from "@/app/components/ui/Badge";
import { Calendar, Filter, RefreshCw, Info, ExternalLink, Clock, Tag } from "lucide-react";

interface Agendamento {
  id: string;
  wl_agendamento_id: string;
  lead_id: string;
  tipo: string;
  data: string;
  hora: string;
  cliente_nome: string;
  cliente_telefone: string;
  produto_ref?: string;
  origem: "automacao" | "loja";
  status: string;
}

const MOCK_AGENDAMENTOS: Agendamento[] = [
  {
    id: "ag_1",
    wl_agendamento_id: "wl_101",
    lead_id: "lead_marianne",
    tipo: "prova",
    data: "2026-09-01",
    hora: "14:00",
    cliente_nome: "Mariana Alencar",
    cliente_telefone: "5585988112233",
    produto_ref: "V-101",
    origem: "automacao",
    status: "ativo",
  },
  {
    id: "ag_2",
    wl_agendamento_id: "wl_102",
    lead_id: "lead_carla",
    tipo: "retirada",
    data: "2026-09-01",
    hora: "16:30",
    cliente_nome: "Carla Mendes",
    cliente_telefone: "5585999445566",
    produto_ref: "V-102",
    origem: "loja",
    status: "ativo",
  },
  {
    id: "ag_3",
    wl_agendamento_id: "wl_103",
    lead_id: "lead_fernanda",
    tipo: "prova",
    data: "2026-09-05",
    hora: "10:00",
    cliente_nome: "Fernanda Lima",
    cliente_telefone: "5585988223344",
    produto_ref: "V-105",
    origem: "automacao",
    status: "ativo",
  },
];

export default function AgendaPage() {
  const [periodo, setPeriodo] = useState<"dia" | "semana" | "mes" | "custom">("mes");
  const [filtroOrigem, setFiltroOrigem] = useState<"todas" | "automacao" | "loja">("todas");
  const [isSyncing, setIsSyncing] = useState(false);

  const agendamentosFiltrados = MOCK_AGENDAMENTOS.filter((a) => {
    if (filtroOrigem !== "todas" && a.origem !== filtroOrigem) return false;
    return true;
  });

  const handleSync = async () => {
    setIsSyncing(true);
    setTimeout(() => {
      setIsSyncing(false);
    }, 800);
  };

  return (
    <section aria-labelledby="agenda-title" className="space-y-5">
      <div
        className="flex items-center gap-3 rounded-[8px] p-4"
        style={{
          background: "var(--slate-l)",
          border: "1px solid rgba(74, 107, 132, 0.2)",
        }}
      >
        <Info className="h-5 w-5 flex-shrink-0" style={{ color: "var(--slate)" }} />
        <div className="text-[12.3px]" style={{ color: "var(--ink2)" }}>
          Visualização apenas. Remarcar, cancelar ou criar manualmente é feito no portal da WebLocação.
        </div>
      </div>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1
            id="agenda-title"
            className="section-heading flex items-center gap-2"
            style={{ color: "var(--text-primary)" }}
          >
            <Calendar className="h-6 w-6" style={{ color: "var(--accent-primary)" }} />
            Agenda
          </h1>
          <p className="section-subtitle">
            Provas e atendimentos, leitura da WebLocação.
          </p>
        </div>

        <button
          id="btn-sync-agenda"
          onClick={handleSync}
          disabled={isSyncing}
          className="glass-btn glass-btn-primary"
        >
          <RefreshCw className={`h-4 w-4 ${isSyncing ? "animate-spin" : ""}`} />
          {isSyncing ? "Sincronizando..." : "Sincronizar Agora"}
        </button>
      </div>

      <div
        className="glass-card flex flex-wrap items-center justify-between gap-4 p-4"
      >
        <div
          className="flex items-center gap-1 rounded-[8px] border p-1 text-xs font-semibold"
          style={{ background: "var(--c2)", borderColor: "var(--line)" }}
        >
          {(["dia", "semana", "mes", "custom"] as const).map((p) => (
            <button
              key={p}
              id={`btn-periodo-${p}`}
              onClick={() => setPeriodo(p)}
              className="rounded-md px-3 py-1.5 capitalize transition-all"
              style={{
                background: periodo === p ? "var(--accent-primary-muted)" : "transparent",
                color: periodo === p ? "var(--ink)" : "var(--text-muted)",
              }}
            >
              {p === "mes" ? "Mês" : p === "custom" ? "Customizado" : p}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <Filter className="h-4 w-4" style={{ color: "var(--text-muted)" }} />
          <span className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>
            Origem:
          </span>
          <select
            id="select-filtro-origem"
            value={filtroOrigem}
            onChange={(e) => setFiltroOrigem(e.target.value as typeof filtroOrigem)}
            className="glass-select"
            style={{ width: "auto" }}
          >
            <option value="todas">Todas as origens</option>
            <option value="automacao">Automação (IA)</option>
            <option value="loja">Balcão / Loja ERP</option>
          </select>
        </div>
      </div>

      <div
        className="glass-card overflow-hidden"
        style={{
          boxShadow: "var(--shadow-md)",
        }}
      >
        <table className="dark-table">
          <thead>
            <tr>
              <th>Data e Hora</th>
              <th>Cliente / Lead</th>
              <th>Tipo</th>
              <th>Produto Ref</th>
              <th>Origem</th>
              <th className="text-right">Ação</th>
            </tr>
          </thead>
          <tbody>
            {agendamentosFiltrados.map((ag) => (
              <tr key={ag.id}>
                <td className="font-medium" style={{ color: "var(--text-primary)" }}>
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4" style={{ color: "var(--text-muted)" }} />
                    <span>{ag.data} às {ag.hora}</span>
                  </div>
                </td>
                <td>
                  <div className="font-semibold" style={{ color: "var(--text-primary)" }}>
                    {ag.cliente_nome}
                  </div>
                  <div className="text-xs" style={{ color: "var(--text-muted)" }}>
                    {ag.cliente_telefone}
                  </div>
                </td>
                <td className="capitalize">
                  <span
                    className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium"
                    style={{
                      background: "var(--line)",
                      color: "var(--text-secondary)",
                    }}
                  >
                    <Tag className="h-3 w-3" style={{ color: "var(--text-muted)" }} />
                    {ag.tipo}
                  </span>
                </td>
                <td className="font-mono text-xs">
                  {ag.produto_ref || "—"}
                </td>
                <td>
                  {ag.origem === "automacao" ? (
                    <Badge variant="success">Automação</Badge>
                  ) : (
                    <Badge variant="neutral">Loja / ERP</Badge>
                  )}
                </td>
                <td className="text-right">
                  <Link
                    href={`/conversas?lead_id=${ag.lead_id}`}
                    className="inline-flex items-center gap-1 text-xs font-semibold hover:underline"
                    style={{ color: "var(--accent-primary)" }}
                  >
                    Ver Lead <ExternalLink className="h-3.5 w-3.5" />
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

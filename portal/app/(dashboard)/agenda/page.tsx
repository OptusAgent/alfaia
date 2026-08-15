"use client";

import { useState } from "react";
import Link from "next/link";
import { Calendar, Filter, RefreshCw, Info, ExternalLink, Clock, Tag } from "lucide-react";

interface Agendamento {
  id: str;
  wl_agendamento_id: str;
  lead_id: str;
  tipo: str;
  data: str;
  hora: str;
  cliente_nome: str;
  cliente_telefone: str;
  produto_ref?: str;
  origem: "automacao" | "loja";
  status: str;
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
    <section aria-labelledby="agenda-title" className="space-y-6">
      {/* Top Banner de Aviso Fixo Visível sem Scroll (AC 4, AC 11.4) */}
      <div className="flex items-center gap-3 rounded-lg border border-amber-200 bg-amber-50 p-4 text-amber-900 shadow-sm">
        <Info className="h-5 w-5 flex-shrink-0 text-amber-600" />
        <div className="text-sm font-medium">
          <strong>Aviso de Integração WebLocação:</strong> Esta tela é <u>somente leitura</u>. Qualquer alteração ou cancelamento de agendamento deve ser efetuado diretamente no portal da WebLocação.
        </div>
      </div>

      {/* Header com Título e Botão de Sincronização */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 id="agenda-title" className="text-xl font-bold text-neutral-900 flex items-center gap-2">
            <Calendar className="h-6 w-6 text-brand-600" />
            Agenda de Atendimentos
          </h1>
          <p className="text-sm text-neutral-500">
            Sincronização bidirecional em tempo real com a WebLocação ERP.
          </p>
        </div>

        <button
          id="btn-sync-agenda"
          onClick={handleSync}
          disabled={isSyncing}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-neutral-800 disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${isSyncing ? "animate-spin" : ""}`} />
          {isSyncing ? "Sincronizando..." : "Sincronizar Agora"}
        </button>
      </div>

      {/* Seletor de Período e Filtro de Origem (AC 1, AC 11.1) */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-neutral-200 bg-white p-4 shadow-sm">
        <div className="flex items-center gap-1 rounded-lg bg-neutral-100 p-1 text-xs font-semibold text-neutral-700">
          {(["dia", "semana", "mes", "custom"] as const).map((p) => (
            <button
              key={p}
              id={`btn-periodo-${p}`}
              onClick={() => setPeriodo(p)}
              className={`rounded-md px-3 py-1.5 capitalize transition ${
                periodo === p ? "bg-white text-brand-700 shadow-sm" : "hover:text-neutral-900"
              }`}
            >
              {p === "mes" ? "Mês" : p === "custom" ? "Customizado" : p}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <Filter className="h-4 w-4 text-neutral-400" />
          <span className="text-xs font-medium text-neutral-500">Origem:</span>
          <select
            id="select-filtro-origem"
            value={filtroOrigem}
            onChange={(e) => setFiltroOrigem(e.target.value as any)}
            className="rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-xs text-neutral-800 focus:border-brand-500 focus:outline-none"
          >
            <option value="todas">Todas as origens</option>
            <option value="automacao">Automação (IA)</option>
            <option value="loja">Balcão / Loja ERP</option>
          </select>
        </div>
      </div>

      {/* Tabela de Agendamentos */}
      <div className="overflow-hidden rounded-xl border border-neutral-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm text-neutral-700">
          <thead className="border-b border-neutral-200 bg-neutral-50 text-xs font-semibold uppercase tracking-wider text-neutral-500">
            <tr>
              <th className="px-6 py-3">Data e Hora</th>
              <th className="px-6 py-3">Cliente / Lead</th>
              <th className="px-6 py-3">Tipo</th>
              <th className="px-6 py-3">Produto Ref</th>
              <th className="px-6 py-3">Origem</th>
              <th className="px-6 py-3 text-right">Ação</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-200">
            {agendamentosFiltrados.map((ag) => (
              <tr key={ag.id} className="hover:bg-neutral-50/80 transition">
                <td className="px-6 py-4 font-medium text-neutral-900">
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-neutral-400" />
                    <span>{ag.data} às {ag.hora}</span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="font-semibold text-neutral-900">{ag.cliente_nome}</div>
                  <div className="text-xs text-neutral-500">{ag.cliente_telefone}</div>
                </td>
                <td className="px-6 py-4 capitalize">
                  <span className="inline-flex items-center gap-1 rounded-md bg-neutral-100 px-2 py-1 text-xs font-medium text-neutral-700">
                    <Tag className="h-3 w-3 text-neutral-400" />
                    {ag.tipo}
                  </span>
                </td>
                <td className="px-6 py-4 font-mono text-xs text-neutral-600">
                  {ag.produto_ref || "—"}
                </td>
                <td className="px-6 py-4">
                  {ag.origem === "automacao" ? (
                    <span className="inline-flex items-center rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-800">
                      Automação
                    </span>
                  ) : (
                    <span className="inline-flex items-center rounded-full bg-slate-200 px-2.5 py-0.5 text-xs font-semibold text-slate-800">
                      Loja / ERP
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 text-right">
                  <Link
                    href={`/conversas?lead_id=${ag.lead_id}`}
                    className="inline-flex items-center gap-1 text-xs font-semibold text-brand-600 hover:text-brand-800 hover:underline"
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

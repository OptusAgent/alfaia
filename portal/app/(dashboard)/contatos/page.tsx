"use client";

import { useState } from "react";
import { Users, Filter, Tag, CheckCircle2, XCircle, Search, RefreshCw } from "lucide-react";

export interface ContatoItem {
  id: string;
  nome: string;
  telefone: string;
  optOut: boolean;
  tags: string[];
  ultimoLeadStatus: string;
  motivoDescarte?: string | null;
}

const CONTATOS_MOCK: ContatoItem[] = [
  {
    id: "c_1",
    nome: "Mariana Souza",
    telefone: "5585999887766",
    optOut: false,
    tags: ["noiva", "outubro_2026", "vestido_sereia"],
    ultimoLeadStatus: "ganho",
  },
  {
    id: "c_2",
    nome: "Carla Mendes",
    telefone: "5585988776655",
    optOut: false,
    tags: ["debutante", "descartado"],
    ultimoLeadStatus: "descartado",
    motivoDescarte: "optou por alugar em outra loja",
  },
  {
    id: "c_3",
    nome: "Fernanda Lima",
    telefone: "5585977665544",
    optOut: true,
    tags: ["madrinha", "opt_out"],
    ultimoLeadStatus: "descartado",
    motivoDescarte: "solicitou remoção de contato",
  },
];

export default function ContatosPage() {
  const [filtroStatus, setFiltroStatus] = useState<string>("todos");
  const [filtroTag, setFiltroTag] = useState<string>("todos");
  const [busca, setBusca] = useState<string>("");

  const contatosFiltrados = CONTATOS_MOCK.filter((c) => {
    if (filtroStatus !== "todos" && c.ultimoLeadStatus !== filtroStatus) return false;
    if (filtroTag !== "todos" && !c.tags.includes(filtroTag)) return false;
    if (busca && !c.nome.toLowerCase().includes(busca.toLowerCase()) && !c.telefone.includes(busca)) return false;
    return true;
  });

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-neutral-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900 flex items-center gap-2.5">
            <Users className="h-7 w-7 text-brand-600" />
            Base de Contatos & Remarketing
          </h1>
          <p className="text-sm text-neutral-500 mt-1">
            Repositório permanente de clientes com tags históricas para campanhas sazonais (PRD §15.1).
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-neutral-600 bg-neutral-100 px-3 py-1.5 rounded-lg border border-neutral-200">
            Total na Base: <strong>{CONTATOS_MOCK.length} contatos</strong>
          </span>
        </div>
      </div>

      {/* Bar de Filtros / Segmentação (AC 2) */}
      <div className="bg-white p-4 rounded-xl border border-neutral-200 shadow-2xs space-y-4">
        <div className="flex items-center gap-2 text-xs font-bold text-neutral-800 uppercase tracking-wider">
          <Filter className="h-4 w-4 text-brand-600" />
          Filtros de Segmentação para Campanhas
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* Busca por Nome/Telefone */}
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-neutral-400" />
            <input
              type="text"
              placeholder="Buscar por nome ou telefone..."
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-neutral-300 focus:outline-hidden focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
            />
          </div>

          {/* Filtro por Status do Úlitmo Lead */}
          <select
            value={filtroStatus}
            onChange={(e) => setFiltroStatus(e.target.value)}
            className="w-full px-3 py-1.5 text-xs rounded-lg border border-neutral-300 focus:outline-hidden focus:border-brand-500 focus:ring-1 focus:ring-brand-500 bg-white"
          >
            <option value="todos">Todos os Status de Lead</option>
            <option value="ganho">Ganho (Contrato Fechado)</option>
            <option value="descartado">Descartado</option>
            <option value="negociando">Em Negociação</option>
          </select>

          {/* Filtro por Tag */}
          <select
            value={filtroTag}
            onChange={(e) => setFiltroTag(e.target.value)}
            className="w-full px-3 py-1.5 text-xs rounded-lg border border-neutral-300 focus:outline-hidden focus:border-brand-500 focus:ring-1 focus:ring-brand-500 bg-white"
          >
            <option value="todos">Todas as Tags</option>
            <option value="noiva">Noiva</option>
            <option value="debutante">Debutante</option>
            <option value="madrinha">Madrinha</option>
            <option value="descartado">Descartado</option>
          </select>
        </div>
      </div>

      {/* Tabela de Contatos Segmentados (AC 1, AC 3) */}
      <div className="bg-white rounded-xl border border-neutral-200 shadow-2xs overflow-hidden">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-neutral-50 text-neutral-600 font-semibold border-b border-neutral-200">
              <th className="py-3 px-4">Nome do Contato</th>
              <th className="py-3 px-4">Telefone</th>
              <th className="py-3 px-4">Último Lead Status</th>
              <th className="py-3 px-4">Tags de Perfil</th>
              <th className="py-3 px-4">Status Campanha</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {contatosFiltrados.map((contato) => (
              <tr key={contato.id} className="hover:bg-neutral-50/80 transition">
                <td className="py-3 px-4 font-bold text-neutral-900">{contato.nome}</td>
                <td className="py-3 px-4 font-mono text-neutral-600">{contato.telefone}</td>
                <td className="py-3 px-4">
                  <span
                    className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full font-semibold text-[11px] ${
                      contato.ultimoLeadStatus === "ganho"
                        ? "bg-emerald-100 text-emerald-800"
                        : contato.ultimoLeadStatus === "descartado"
                        ? "bg-rose-100 text-rose-800"
                        : "bg-amber-100 text-amber-800"
                    }`}
                  >
                    {contato.ultimoLeadStatus.toUpperCase()}
                  </span>
                </td>
                <td className="py-3 px-4">
                  <div className="flex flex-wrap gap-1">
                    {contato.tags.map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center gap-0.5 bg-neutral-100 text-neutral-700 border border-neutral-200 px-2 py-0.5 rounded-md text-[10px] font-medium"
                      >
                        <Tag className="h-2.5 w-2.5 text-neutral-500" />
                        {tag}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="py-3 px-4">
                  {contato.optOut ? (
                    <span className="inline-flex items-center gap-1 text-rose-600 font-semibold text-[11px]">
                      <XCircle className="h-3.5 w-3.5" /> Opt-Out
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-emerald-600 font-semibold text-[11px]">
                      <CheckCircle2 className="h-3.5 w-3.5" /> Elegível
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

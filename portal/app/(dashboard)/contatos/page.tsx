"use client";

import { useState } from "react";
import { Badge } from "@/app/components/ui/Badge";
import { Users, Filter, Tag, CheckCircle2, XCircle, Search } from "lucide-react";

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
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div
        className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5"
        style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.06)" }}
      >
        <div>
          <h1
            className="text-2xl font-bold font-display flex items-center gap-2.5"
            style={{ color: "var(--text-primary)" }}
          >
            <Users className="h-7 w-7" style={{ color: "var(--accent-primary)" }} />
            Base de Contatos & Remarketing
          </h1>
          <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
            Repositório permanente de clientes com tags históricas para campanhas sazonais.
          </p>
        </div>
        <Badge variant="neutral">
          Total na Base: <strong>{CONTATOS_MOCK.length} contatos</strong>
        </Badge>
      </div>

      {/* Filtros */}
      <div className="glass-card p-4 space-y-4">
        <div
          className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider"
          style={{ color: "var(--text-secondary)" }}
        >
          <Filter className="h-4 w-4" style={{ color: "var(--accent-primary)" }} />
          Filtros de Segmentação
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* Search */}
          <div className="relative">
            <Search
              className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4"
              style={{ color: "var(--text-muted)" }}
            />
            <input
              type="text"
              placeholder="Buscar por nome ou telefone..."
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              className="glass-input pl-9 text-xs"
            />
          </div>

          {/* Status Filter */}
          <select
            value={filtroStatus}
            onChange={(e) => setFiltroStatus(e.target.value)}
            className="glass-select"
          >
            <option value="todos">Todos os Status de Lead</option>
            <option value="ganho">Ganho (Contrato Fechado)</option>
            <option value="descartado">Descartado</option>
            <option value="negociando">Em Negociação</option>
          </select>

          {/* Tag Filter */}
          <select
            value={filtroTag}
            onChange={(e) => setFiltroTag(e.target.value)}
            className="glass-select"
          >
            <option value="todos">Todas as Tags</option>
            <option value="noiva">Noiva</option>
            <option value="debutante">Debutante</option>
            <option value="madrinha">Madrinha</option>
            <option value="descartado">Descartado</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div
        className="rounded-xl overflow-hidden"
        style={{
          background: "rgba(255, 255, 255, 0.02)",
          border: "1px solid rgba(255, 255, 255, 0.06)",
        }}
      >
        <table className="dark-table">
          <thead>
            <tr>
              <th>Nome do Contato</th>
              <th>Telefone</th>
              <th>Último Lead Status</th>
              <th>Tags de Perfil</th>
              <th>Status Campanha</th>
              <th className="text-right">Ações LGPD</th>
            </tr>
          </thead>
          <tbody>
            {contatosFiltrados.map((contato) => (
              <tr key={contato.id}>
                <td className="font-bold" style={{ color: "var(--text-primary)" }}>
                  {contato.nome}
                </td>
                <td className="font-mono">{contato.telefone}</td>
                <td>
                  <Badge
                    variant={
                      contato.ultimoLeadStatus === "ganho"
                        ? "success"
                        : contato.ultimoLeadStatus === "descartado"
                        ? "danger"
                        : "warning"
                    }
                  >
                    {contato.ultimoLeadStatus.toUpperCase()}
                  </Badge>
                </td>
                <td>
                  <div className="flex flex-wrap gap-1">
                    {contato.tags.map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center gap-0.5 px-2 py-0.5 rounded-md text-[10px] font-medium"
                        style={{
                          background: "rgba(255, 255, 255, 0.06)",
                          color: "var(--text-secondary)",
                          border: "1px solid rgba(255, 255, 255, 0.06)",
                        }}
                      >
                        <Tag className="h-2.5 w-2.5" style={{ color: "var(--text-muted)" }} />
                        {tag}
                      </span>
                    ))}
                  </div>
                </td>
                <td>
                  {contato.optOut ? (
                    <Badge variant="danger" icon={<XCircle className="h-3 w-3" />}>
                      Opt-Out
                    </Badge>
                  ) : (
                    <Badge variant="success" icon={<CheckCircle2 className="h-3 w-3" />}>
                      Elegível
                    </Badge>
                  )}
                </td>
                <td className="text-right space-x-2">
                  <button
                    onClick={() => alert(`Dados de ${contato.nome} exportados em JSON com log de auditoria`)}
                    className="glass-btn glass-btn-ghost text-[10px] px-2.5 py-1"
                  >
                    Exportar
                  </button>
                  <button
                    onClick={() => alert(`Contato ${contato.nome} excluído em cascata LGPD`)}
                    className="glass-btn glass-btn-danger text-[10px] px-2.5 py-1"
                  >
                    Excluir
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

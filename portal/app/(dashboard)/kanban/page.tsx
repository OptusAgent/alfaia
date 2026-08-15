"use client";

import { useState } from "react";
import Link from "next/link";
import { Badge } from "@/app/components/ui/Badge";
import {
  Kanban as KanbanIcon,
  Calendar,
  DollarSign,
  Clock,
  MessageSquare,
} from "lucide-react";

export type StatusLead =
  | "novo"
  | "orcamento"
  | "follow_up"
  | "negociando"
  | "agendado"
  | "descartado";

export interface LeadKanban {
  id: string;
  nome: string;
  telefone: string;
  status: StatusLead;
  evento?: string;
  valorEstimado?: number;
  tempoUltimoContato: string;
  statusAlteradoPor: "ia" | "humano" | "sistema";
}

const COLUNAS: { id: StatusLead; titulo: string; cor: string }[] = [
  { id: "novo", titulo: "Novo", cor: "#3B82F6" },
  { id: "orcamento", titulo: "Orçamento", cor: "#F59E0B" },
  { id: "follow_up", titulo: "Follow-up", cor: "#8B5CF6" },
  { id: "negociando", titulo: "Negociando", cor: "#6366F1" },
  { id: "agendado", titulo: "Agendado", cor: "#10B981" },
  { id: "descartado", titulo: "Descartado", cor: "#F43F5E" },
];

const MOCK_LEADS: LeadKanban[] = [
  {
    id: "lead_1",
    nome: "Mariana Silva",
    telefone: "(85) 98811-2233",
    status: "novo",
    evento: "Casamento • Noiva",
    valorEstimado: 1200,
    tempoUltimoContato: "há 10 min",
    statusAlteradoPor: "ia",
  },
  {
    id: "lead_2",
    nome: "Carla Mendes",
    telefone: "(85) 99944-5566",
    status: "orcamento",
    evento: "Formatura • Formando",
    valorEstimado: 550,
    tempoUltimoContato: "há 45 min",
    statusAlteradoPor: "ia",
  },
  {
    id: "lead_3",
    nome: "Fernanda Lima",
    telefone: "(85) 98822-3344",
    status: "orcamento",
    evento: "Gala • Convidada",
    valorEstimado: 480,
    tempoUltimoContato: "há 2 horas",
    statusAlteradoPor: "ia",
  },
  {
    id: "lead_4",
    nome: "Beatriz Souza",
    telefone: "(85) 99711-8899",
    status: "agendado",
    evento: "Casamento • Madrinha",
    valorEstimado: 680,
    tempoUltimoContato: "há 1 dia",
    statusAlteradoPor: "humano",
  },
];

export default function KanbanPage() {
  const [leads, setLeads] = useState<LeadKanban[]>(MOCK_LEADS);
  const [draggedLeadId, setDraggedLeadId] = useState<string | null>(null);

  const moverStatus = (leadId: string, novoStatus: StatusLead) => {
    setLeads((prev) =>
      prev.map((l) => {
        if (l.id === leadId) {
          return {
            ...l,
            status: novoStatus,
            statusAlteradoPor: "humano",
            tempoUltimoContato: "agora (manual)",
          };
        }
        return l;
      })
    );
  };

  const handleDragStart = (e: React.DragEvent, leadId: string) => {
    setDraggedLeadId(leadId);
    e.dataTransfer.setData("text/plain", leadId);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent, targetStatus: StatusLead) => {
    e.preventDefault();
    const leadId = e.dataTransfer.getData("text/plain") || draggedLeadId;
    if (leadId) {
      moverStatus(leadId, targetStatus);
    }
    setDraggedLeadId(null);
  };

  return (
    <section aria-labelledby="kanban-title" className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1
            id="kanban-title"
            className="text-xl font-bold font-display flex items-center gap-2"
            style={{ color: "var(--text-primary)" }}
          >
            <KanbanIcon className="h-6 w-6" style={{ color: "var(--accent-primary)" }} />
            Funil de Atendimento
          </h1>
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>
            Acompanhe a jornada dos leads pelas etapas do funil de conversão.
          </p>
        </div>

        <Badge variant="neutral">
          Total no Funil: <strong style={{ color: "var(--accent-primary)" }}>{leads.length}</strong> leads
        </Badge>
      </div>

      {/* Board */}
      <div className="flex gap-4 overflow-x-auto pb-6 max-w-full">
        {COLUNAS.map((coluna) => {
          const leadsDaColuna = leads.filter((l) => l.status === coluna.id);

          return (
            <div
              key={coluna.id}
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, coluna.id)}
              className="flex flex-col rounded-xl min-h-[500px] min-w-[280px] max-w-[340px] flex-1 flex-shrink-0 p-3 transition-all"
              style={{
                background: "rgba(255, 255, 255, 0.02)",
                border: "1px solid rgba(255, 255, 255, 0.06)",
                borderTopWidth: "3px",
                borderTopColor: coluna.cor,
              }}
            >
              {/* Column Header */}
              <div
                className="flex items-center justify-between pb-3 mb-2"
                style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.06)" }}
              >
                <h2
                  className="text-xs font-bold uppercase tracking-wider"
                  style={{ color: "var(--text-secondary)" }}
                >
                  {coluna.titulo}
                </h2>
                <span
                  className="rounded-full px-2 py-0.5 text-xs font-bold"
                  style={{
                    background: "rgba(255, 255, 255, 0.06)",
                    color: "var(--text-muted)",
                  }}
                >
                  {leadsDaColuna.length}
                </span>
              </div>

              {/* Cards */}
              <div className="space-y-3 flex-1">
                {leadsDaColuna.map((lead) => (
                  <div
                    key={lead.id}
                    draggable
                    onDragStart={(e) => handleDragStart(e, lead.id)}
                    className="group relative rounded-lg p-3 cursor-grab active:cursor-grabbing space-y-2.5 transition-all"
                    style={{
                      background: "rgba(255, 255, 255, 0.04)",
                      border: "1px solid rgba(255, 255, 255, 0.06)",
                    }}
                  >
                    {/* Top */}
                    <div className="flex items-start justify-between gap-2">
                      <div
                        className="font-bold text-sm"
                        style={{ color: "var(--text-primary)" }}
                      >
                        {lead.nome}
                      </div>
                      {lead.statusAlteradoPor === "humano" ? (
                        <Badge variant="purple">Humano</Badge>
                      ) : (
                        <Badge variant="success">IA</Badge>
                      )}
                    </div>

                    {/* Metadata */}
                    <div className="text-xs space-y-1" style={{ color: "var(--text-secondary)" }}>
                      {lead.evento && (
                        <div className="flex items-center gap-1.5">
                          <Calendar className="h-3.5 w-3.5 flex-shrink-0" style={{ color: "var(--text-muted)" }} />
                          <span className="truncate">{lead.evento}</span>
                        </div>
                      )}

                      {lead.valorEstimado && (
                        <div className="flex items-center gap-1.5 font-semibold" style={{ color: "var(--accent-primary)" }}>
                          <DollarSign className="h-3.5 w-3.5 flex-shrink-0" />
                          <span>R$ {lead.valorEstimado.toFixed(2)}</span>
                        </div>
                      )}

                      <div
                        className="flex items-center gap-1.5 text-[11px] pt-1"
                        style={{
                          color: "var(--text-muted)",
                          borderTop: "1px solid rgba(255, 255, 255, 0.04)",
                        }}
                      >
                        <Clock className="h-3 w-3 flex-shrink-0" />
                        <span>{lead.tempoUltimoContato}</span>
                      </div>
                    </div>

                    {/* Actions */}
                    <div
                      className="pt-2 flex items-center justify-between text-xs"
                      style={{ borderTop: "1px solid rgba(255, 255, 255, 0.04)" }}
                    >
                      <Link
                        href={`/conversas?lead_id=${lead.id}`}
                        className="inline-flex items-center gap-1 text-[11px] font-medium hover:underline"
                        style={{ color: "var(--accent-primary)" }}
                      >
                        <MessageSquare className="h-3 w-3" /> Abrir Chat
                      </Link>

                      <select
                        aria-label={`Mover lead ${lead.nome}`}
                        value={lead.status}
                        onChange={(e) => moverStatus(lead.id, e.target.value as StatusLead)}
                        className="glass-select text-[10px] py-0.5 px-1"
                        style={{ width: "auto" }}
                      >
                        {COLUNAS.map((c) => (
                          <option key={c.id} value={c.id}>
                            Mover para {c.titulo}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                ))}

                {leadsDaColuna.length === 0 && (
                  <div
                    className="h-24 flex items-center justify-center rounded-lg text-xs italic"
                    style={{
                      border: "1px dashed rgba(255, 255, 255, 0.1)",
                      color: "var(--text-muted)",
                    }}
                  >
                    Nenhum lead nesta etapa
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

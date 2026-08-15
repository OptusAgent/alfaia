"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Kanban as KanbanIcon,
  User,
  Calendar,
  DollarSign,
  Clock,
  ChevronRight,
  ChevronLeft,
  MessageSquare,
  AlertCircle,
  CheckCircle2,
  XCircle,
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

const COLUNAS: { id: StatusLead; titulo: string; corBorder: string; corBg: string }[] = [
  { id: "novo", titulo: "Novo", corBorder: "border-blue-400", corBg: "bg-blue-50/50" },
  { id: "orcamento", titulo: "Orçamento", corBorder: "border-amber-400", corBg: "bg-amber-50/50" },
  { id: "follow_up", titulo: "Follow-up", corBorder: "border-purple-400", corBg: "bg-purple-50/50" },
  { id: "negociando", titulo: "Negociando", corBorder: "border-indigo-400", corBg: "bg-indigo-50/50" },
  { id: "agendado", titulo: "Agendado", corBorder: "border-teal-400", corBg: "bg-teal-50/50" },
  { id: "descartado", titulo: "Descartado", corBorder: "border-rose-400", corBg: "bg-rose-50/50" },
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
          // Gravação explícita do autor humano (AC 2, AC 10.5)
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
      {/* Header com Título e Estatísticas */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 id="kanban-title" className="text-xl font-bold text-neutral-900 flex items-center gap-2">
            <KanbanIcon className="h-6 w-6 text-brand-600" />
            Funil de Atendimento (Kanban)
          </h1>
          <p className="text-sm text-neutral-500">
            Acompanhe a jornada dos leads pelas etapas do funil de conversão.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="inline-flex items-center gap-1.5 rounded-lg border border-neutral-200 bg-white px-3 py-1.5 text-xs font-semibold text-neutral-700 shadow-sm">
            Total no Funil: <strong className="text-brand-600">{leads.length}</strong> leads
          </span>
        </div>
      </div>

      {/* Board Kanban Responsivo */}
      <div className="flex gap-4 overflow-x-auto pb-6 max-w-full">
        {COLUNAS.map((coluna) => {
          const leadsDaColuna = leads.filter((l) => l.status === coluna.id);

          return (
            <div
              key={coluna.id}
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, coluna.id)}
              className={`flex flex-col rounded-xl border-t-4 ${coluna.corBorder} ${coluna.corBg} border-x border-b border-neutral-200 p-3 min-h-[500px] min-w-[280px] max-w-[340px] flex-1 flex-shrink-0 shadow-sm transition`}
            >
              {/* Header da Coluna */}
              <div className="flex items-center justify-between pb-3 mb-2 border-b border-neutral-200/80">
                <h2 className="text-xs font-bold uppercase tracking-wider text-neutral-800">
                  {coluna.titulo}
                </h2>
                <span className="rounded-full bg-white px-2 py-0.5 text-xs font-bold text-neutral-600 shadow-xs border border-neutral-200">
                  {leadsDaColuna.length}
                </span>
              </div>

              {/* Lista de Cards da Coluna */}
              <div className="space-y-3 flex-1">
                {leadsDaColuna.map((lead) => (
                  <div
                    key={lead.id}
                    draggable
                    onDragStart={(e) => handleDragStart(e, lead.id)}
                    className="group relative rounded-lg border border-neutral-200 bg-white p-3 shadow-xs hover:shadow-md transition cursor-grab active:cursor-grabbing space-y-2.5"
                  >
                    {/* Top Card: Nome e Origem */}
                    <div className="flex items-start justify-between gap-2">
                      <div className="font-bold text-neutral-900 text-sm group-hover:text-brand-600 transition">
                        {lead.nome}
                      </div>
                      {lead.statusAlteradoPor === "humano" ? (
                        <span className="inline-flex items-center rounded-md bg-purple-100 px-1.5 py-0.5 text-[10px] font-bold text-purple-800" title="Movimentado manualmente por atendente">
                          Humano
                        </span>
                      ) : (
                        <span className="inline-flex items-center rounded-md bg-emerald-100 px-1.5 py-0.5 text-[10px] font-bold text-emerald-800" title="Movimentado por automação IA">
                          IA
                        </span>
                      )}
                    </div>

                    {/* Metadados do Lead (AC 4) */}
                    <div className="text-xs text-neutral-600 space-y-1">
                      {lead.evento && (
                        <div className="flex items-center gap-1.5 text-neutral-700">
                          <Calendar className="h-3.5 w-3.5 text-neutral-400 flex-shrink-0" />
                          <span className="truncate">{lead.evento}</span>
                        </div>
                      )}

                      {lead.valorEstimado && (
                        <div className="flex items-center gap-1.5 font-semibold text-emerald-700">
                          <DollarSign className="h-3.5 w-3.5 text-emerald-500 flex-shrink-0" />
                          <span>R$ {lead.valorEstimado.toFixed(2)}</span>
                        </div>
                      )}

                      <div className="flex items-center gap-1.5 text-[11px] text-neutral-400 pt-1 border-t border-neutral-100">
                        <Clock className="h-3 w-3 flex-shrink-0" />
                        <span>{lead.tempoUltimoContato}</span>
                      </div>
                    </div>

                    {/* Controles de Acessibilidade Keyboard WCAG 2.1 AA (Task 5) */}
                    <div className="pt-2 flex items-center justify-between border-t border-neutral-100 text-xs">
                      <Link
                        href={`/conversas?lead_id=${lead.id}`}
                        className="inline-flex items-center gap-1 text-[11px] font-medium text-brand-600 hover:underline"
                      >
                        <MessageSquare className="h-3 w-3" /> Abrir Chat
                      </Link>

                      {/* Dropdown de Acessibilidade por Teclado */}
                      <select
                        aria-label={`Mover lead ${lead.nome}`}
                        value={lead.status}
                        onChange={(e) => moverStatus(lead.id, e.target.value as StatusLead)}
                        className="text-[10px] rounded border border-neutral-200 bg-neutral-50 px-1 py-0.5 text-neutral-700 focus:outline-none"
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
                  <div className="h-24 flex items-center justify-center rounded-lg border border-dashed border-neutral-300/70 text-xs text-neutral-400 italic">
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

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
  { id: "novo", titulo: "Novo", cor: "var(--dim)" },
  { id: "orcamento", titulo: "Orçamento", cor: "var(--warn)" },
  { id: "follow_up", titulo: "Follow-up", cor: "var(--bad)" },
  { id: "negociando", titulo: "Negociando", cor: "var(--gold-ink)" },
  { id: "agendado", titulo: "Agendado", cor: "var(--teal-ink)" },
  { id: "descartado", titulo: "Descartado", cor: "var(--ice-ink)" },
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
    <section aria-labelledby="kanban-title" className="space-y-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1
            id="kanban-title"
            className="section-heading flex items-center gap-2"
            style={{ color: "var(--text-primary)" }}
          >
            <KanbanIcon className="h-6 w-6" style={{ color: "var(--accent-primary)" }} />
            Pipeline de leads
          </h1>
          <p className="section-subtitle">
            Todo lead que chega, do primeiro oi ao contrato.
          </p>
        </div>

        <Badge variant="neutral">
          Total no quadro: <strong style={{ color: "var(--accent-primary)" }}>{leads.length}</strong> leads
        </Badge>
      </div>

      <div className="fluir-tiles">
        <div className="fluir-tile t-mint">
          <div className="label">
            Leads ativos
          </div>
          <div className="value">{leads.filter((l) => l.status !== "descartado").length}</div>
          <div className="desc">no quadro agora</div>
        </div>
        <div className="fluir-tile t-pump">
          <div className="label">
            Aguardando follow-up
          </div>
          <div className="value">{leads.filter((l) => l.status === "follow_up").length}</div>
          <div className="desc">botão de disparo ativo</div>
        </div>
        <div className="fluir-tile t-ice">
          <div className="label">
            Provas agendadas
          </div>
          <div className="value">{leads.filter((l) => l.status === "agendado").length}</div>
          <div className="desc">pela automação</div>
        </div>
      </div>

      <div className="flex max-w-full gap-3 overflow-x-auto pb-3">
        {COLUNAS.map((coluna) => {
          const leadsDaColuna = leads.filter((l) => l.status === coluna.id);

          return (
            <div
              key={coluna.id}
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, coluna.id)}
              className="flex min-h-[560px] min-w-[236px] flex-1 flex-shrink-0 flex-col rounded-[14px] p-0 transition-all"
              style={{
                background: "var(--c2)",
                border: "1px solid var(--line)",
                borderRadius: "var(--r)",
              }}
            >
              <div
                className="flex items-center gap-2 px-[14px] py-3"
                style={{ borderBottom: "1px solid var(--line)" }}
              >
                <span className="h-2 w-2 rounded-full" style={{ background: coluna.cor }} />
                <h2
                  className="flex-1 text-[12.3px] font-bold"
                  style={{ color: "var(--text-secondary)" }}
                >
                  {coluna.titulo}
                </h2>
                <span
                  className="rounded-full border px-2 py-0.5 font-mono text-[10.5px]"
                  style={{
                    background: "var(--card)",
                    borderColor: "var(--line)",
                    color: "var(--text-muted)",
                  }}
                >
                  {leadsDaColuna.length}
                </span>
              </div>

              <div className="flex flex-1 flex-col gap-[9px] overflow-y-auto p-[10px]">
                {leadsDaColuna.map((lead) => (
                  <div
                    key={lead.id}
                    draggable
                    onDragStart={(e) => handleDragStart(e, lead.id)}
                    className="group relative cursor-grab space-y-2 rounded-[8px] p-3 transition-all active:cursor-grabbing"
                    style={{
                      background: "var(--card)",
                      border: "1px solid var(--line)",
                      borderRadius: "12px",
                      boxShadow: "var(--shadow-md)",
                    }}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex min-w-0 items-center gap-2">
                        <span
                          className="grid h-[26px] w-[26px] flex-none place-items-center rounded-full text-[10px] font-bold"
                          style={{ background: "var(--line-2)", color: "var(--ink-2)" }}
                        >
                          {lead.nome.split(" ").map((x) => x[0]).slice(0, 2).join("")}
                        </span>
                        <div
                          className="truncate text-[12.4px] font-bold"
                          style={{ color: "var(--text-primary)" }}
                        >
                          {lead.nome}
                        </div>
                      </div>
                      {lead.statusAlteradoPor === "humano" ? (
                        <Badge variant="purple">Humano</Badge>
                      ) : (
                        <Badge variant="success">IA</Badge>
                      )}
                    </div>

                    <div className="space-y-1 text-[11.5px]" style={{ color: "var(--text-muted)" }}>
                      {lead.evento && (
                        <div className="flex items-center gap-1.5">
                          <Calendar className="h-3.5 w-3.5 flex-shrink-0" style={{ color: "var(--text-muted)" }} />
                          <span className="truncate">{lead.evento}</span>
                        </div>
                      )}

                      {lead.valorEstimado && (
                        <div className="flex items-center gap-1.5 font-semibold" style={{ color: "var(--accent-primary)" }}>
                          <DollarSign className="h-3.5 w-3.5 flex-shrink-0" />
                          <span>R$ {lead.valorEstimado.toFixed(2).replace(".", ",")}</span>
                        </div>
                      )}

                      <div
                        className="flex items-center gap-1.5 pt-2 font-mono text-[9.5px]"
                        style={{
                          color: "var(--text-muted)",
                          borderTop: "1px solid var(--line2)",
                        }}
                      >
                        <Clock className="h-3 w-3 flex-shrink-0" />
                        <span>{lead.tempoUltimoContato}</span>
                      </div>
                    </div>

                    <div
                      className="pt-2 flex items-center justify-between text-xs"
                      style={{ borderTop: "1px solid var(--line2)" }}
                    >
                      <Link
                        href={`/conversas?lead_id=${lead.id}`}
                        className="inline-flex items-center gap-1 text-[11px] font-medium hover:underline"
                        style={{ color: "var(--teal-ink)" }}
                      >
                        <MessageSquare className="h-3 w-3" /> Abrir Chat
                      </Link>

                      <select
                        aria-label={`Mover lead ${lead.nome}`}
                        value={lead.status}
                        onChange={(e) => moverStatus(lead.id, e.target.value as StatusLead)}
                        className="glass-select py-0.5 pl-2 pr-7 text-[10px]"
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
                    className="flex h-24 items-center justify-center rounded-[8px] text-xs italic"
                    style={{
                      border: "1px dashed var(--line)",
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

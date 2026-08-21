"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Badge } from "@/app/components/ui/Badge";
import {
  Kanban as KanbanIcon,
  Calendar,
  DollarSign,
  Clock,
  MessageSquare,
} from "lucide-react";
import { createClient } from "@/lib/supabase/client";

export type StatusLead =
  | "novo"
  | "qualificando"
  | "orcamento"
  | "follow_up"
  | "negociando"
  | "agendado"
  | "ganho"
  | "descartado";

export interface LeadKanban {
  id: string;
  nome: string;
  telefone: string;
  status: StatusLead;
  evento?: string;
  valorEstimado?: number;
  tempoUltimoContato: string;
  statusAlteradoPor: "ia" | "atendente" | "sistema";
}

interface DbLeadItem {
  id: string;
  status: StatusLead;
  status_alterado_por: "ia" | "atendente" | "sistema" | null;
  evento_tipo?: string | null;
  papel?: string | null;
  peca_interesse?: string | null;
  valor_estimado?: number | null;
  ultimo_contato_em?: string | null;
  contatos?: { nome?: string | null; telefone?: string | null } | null;
}

const COLUNAS: { id: StatusLead; titulo: string; cor: string }[] = [
  { id: "novo", titulo: "Novo", cor: "var(--dim)" },
  { id: "qualificando", titulo: "Qualificando", cor: "var(--ice-ink)" },
  { id: "orcamento", titulo: "Orçamento", cor: "var(--warn)" },
  { id: "follow_up", titulo: "Follow-up", cor: "var(--bad)" },
  { id: "negociando", titulo: "Negociando", cor: "var(--gold-ink)" },
  { id: "agendado", titulo: "Agendado", cor: "var(--teal-ink)" },
  { id: "ganho", titulo: "Ganho", cor: "var(--pump-ink)" },
  { id: "descartado", titulo: "Descartado", cor: "var(--rose-ink)" },
];

function tempoRelativo(iso: string | null | undefined): string {
  if (!iso) return "sem contato registrado";
  const diffMs = Date.now() - new Date(iso).getTime();
  if (Number.isNaN(diffMs)) return "sem contato registrado";
  const min = Math.floor(diffMs / 60000);
  if (min < 1) return "agora mesmo";
  if (min < 60) return `há ${min} min`;
  const horas = Math.floor(min / 60);
  if (horas < 24) return `há ${horas} ${horas === 1 ? "hora" : "horas"}`;
  const dias = Math.floor(horas / 24);
  return `há ${dias} ${dias === 1 ? "dia" : "dias"}`;
}

function mapearLead(item: DbLeadItem): LeadKanban {
  const contato = item.contatos || {};
  const eventoPartes = [item.evento_tipo, item.papel].filter(Boolean);
  return {
    id: item.id,
    nome: contato.nome || "Lead sem nome",
    telefone: contato.telefone || "",
    status: item.status,
    evento: eventoPartes.length > 0 ? eventoPartes.join(" • ") : item.peca_interesse || undefined,
    valorEstimado: item.valor_estimado ?? undefined,
    tempoUltimoContato: tempoRelativo(item.ultimo_contato_em),
    statusAlteradoPor: item.status_alterado_por || "sistema",
  };
}

export default function KanbanPage() {
  const [leads, setLeads] = useState<LeadKanban[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [tenantId, setTenantId] = useState("");
  const [draggedLeadId, setDraggedLeadId] = useState<string | null>(null);
  const supabase = useMemo(() => createClient(), []);

  const buscarLeads = useCallback(
    async (activeTenantId: string) => {
      if (!activeTenantId) {
        setLeads([]);
        setCarregando(false);
        return;
      }

      const { data, error } = await supabase
        .from("leads")
        .select(
          `
          id,
          status,
          status_alterado_por,
          evento_tipo,
          papel,
          peca_interesse,
          valor_estimado,
          ultimo_contato_em,
          contatos ( nome, telefone )
        `
        )
        .eq("tenant_id", activeTenantId)
        .order("atualizado_em", { ascending: false });

      if (error) {
        console.error("Falha ao buscar leads reais do Kanban:", error);
        setCarregando(false);
        return;
      }

      setLeads(((data || []) as unknown as DbLeadItem[]).map(mapearLead));
      setCarregando(false);
    },
    [supabase]
  );

  useEffect(() => {
    let channel: ReturnType<typeof supabase.channel> | null = null;
    let mounted = true;

    async function iniciar() {
      const res = await fetch("/api/tenant/active", { cache: "no-store" });
      if (!res.ok) {
        setCarregando(false);
        return;
      }
      const data = await res.json();
      const activeTenantId = String(data.tenant_id || "");
      if (!mounted) return;
      setTenantId(activeTenantId);
      await buscarLeads(activeTenantId);

      if (!activeTenantId) return;
      channel = supabase
        .channel(`realtime-kanban-leads-${activeTenantId}`)
        .on(
          "postgres_changes",
          { event: "*", schema: "public", table: "leads", filter: `tenant_id=eq.${activeTenantId}` },
          () => {
            void buscarLeads(activeTenantId);
          }
        )
        .subscribe();
    }
    iniciar();

    return () => {
      mounted = false;
      if (channel) void supabase.removeChannel(channel);
    };
  }, [buscarLeads, supabase]);

  const moverStatus = async (leadId: string, novoStatus: StatusLead) => {
    const leadAtual = leads.find((l) => l.id === leadId);
    if (!leadAtual || leadAtual.status === novoStatus || !tenantId) return;

    // MV5 (mesma regra aplicada à IA em status_transition_service, story 3.5/6.6): descarte
    // exige motivo textual — vale para movimentação humana também, não só automática.
    let motivo: string | null = null;
    if (novoStatus === "descartado") {
      motivo = window.prompt("Motivo do descarte (obrigatório):", "");
      if (!motivo || !motivo.trim()) return;
    }

    const statusAnterior = leadAtual.status;
    const agoraIso = new Date().toISOString();

    // Atualização otimista — reverte com um novo fetch se a escrita real falhar.
    setLeads((prev) =>
      prev.map((l) =>
        l.id === leadId
          ? { ...l, status: novoStatus, statusAlteradoPor: "atendente", tempoUltimoContato: "agora (manual)" }
          : l
      )
    );

    const { error } = await supabase
      .from("leads")
      .update({
        status: novoStatus,
        status_alterado_por: "atendente",
        status_alterado_em: agoraIso,
        ...(novoStatus === "descartado" ? { motivo_descarte: motivo } : {}),
      })
      .eq("id", leadId)
      .eq("tenant_id", tenantId);

    if (error) {
      console.error("Falha ao mover lead no Kanban:", error);
      await buscarLeads(tenantId);
      return;
    }

    // AC 6 (story 6.6): toda movimentação grava lead_eventos, autor e motivo.
    const { error: erroEvento } = await supabase.from("lead_eventos").insert({
      tenant_id: tenantId,
      lead_id: leadId,
      tipo: "status_alterado",
      de: statusAnterior,
      para: novoStatus,
      autor: "atendente",
      motivo,
    });
    if (erroEvento) {
      console.error("Falha ao registrar lead_evento da movimentação manual:", erroEvento);
    }
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
      void moverStatus(leadId, targetStatus);
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
          <div className="value">{leads.filter((l) => l.status !== "descartado" && l.status !== "ganho").length}</div>
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

      {carregando && (
        <div className="rounded-[14px] p-6 text-center text-sm" style={{ color: "var(--text-muted)", border: "1px dashed var(--line)" }}>
          Carregando leads reais...
        </div>
      )}

      {!carregando && !tenantId && (
        <div className="rounded-[14px] p-6 text-center text-sm" style={{ color: "var(--text-muted)", border: "1px dashed var(--line)" }}>
          Nenhum tenant ativo encontrado para carregar o quadro.
        </div>
      )}

      {!carregando && tenantId && (
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
                        {lead.statusAlteradoPor === "atendente" ? (
                          <Badge variant="purple">Humano</Badge>
                        ) : lead.statusAlteradoPor === "ia" ? (
                          <Badge variant="success">IA</Badge>
                        ) : (
                          <Badge variant="neutral">Sistema</Badge>
                        )}
                      </div>

                      <div className="space-y-1 text-[11.5px]" style={{ color: "var(--text-muted)" }}>
                        {lead.evento && (
                          <div className="flex items-center gap-1.5">
                            <Calendar className="h-3.5 w-3.5 flex-shrink-0" style={{ color: "var(--text-muted)" }} />
                            <span className="truncate">{lead.evento}</span>
                          </div>
                        )}

                        {lead.valorEstimado != null && (
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
                          onChange={(e) => void moverStatus(lead.id, e.target.value as StatusLead)}
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
      )}
    </section>
  );
}

"use client";

import {
  UserPlus,
  ArrowRightLeft,
  Heart,
  Clock,
  Headphones,
  Calendar,
  Trash2,
  RotateCcw,
  AlertTriangle,
  FileText,
  Tag,
} from "lucide-react";

export interface EventoTimeline {
  id: string | number;
  tipo:
    | "lead_criado"
    | "status_mudou"
    | "interesse_alterado"
    | "followup_enviado"
    | "transbordo_aberto"
    | "transbordo_fechado"
    | "transbordo_assumido"
    | "transbordo_devolvido"
    | "agendou"
    | "descartado"
    | "reaberto"
    | "divergencia_ia_humano"
    | "nota";
  de?: string;
  para?: string;
  autor?: "ia" | "humano" | "sistema";
  motivo?: string;
  detalhe?: Record<string, unknown>;
  criado_em: string;
}

interface LeadTimelineProps {
  leadId?: string;
  nomeLead: string;
  tags?: string[];
  eventos: EventoTimeline[];
}

const ICON_COLORS: Record<string, string> = {
  lead_criado: "var(--accent-primary)",
  status_mudou: "var(--accent-blue)",
  interesse_alterado: "#EC4899",
  followup_enviado: "var(--accent-amber)",
  transbordo_aberto: "var(--accent-purple)",
  transbordo_fechado: "var(--accent-purple)",
  transbordo_assumido: "var(--accent-purple)",
  transbordo_devolvido: "var(--accent-purple)",
  agendou: "var(--accent-primary)",
  descartado: "var(--accent-coral)",
  reaberto: "#06B6D4",
  divergencia_ia_humano: "var(--accent-amber)",
  nota: "var(--text-muted)",
};

export default function LeadTimeline({ nomeLead, tags = [], eventos }: LeadTimelineProps) {
  const renderIconeEvento = (tipo: EventoTimeline["tipo"]) => {
    const color = ICON_COLORS[tipo] || "var(--text-muted)";
    const props = { className: "h-4 w-4", style: { color } };

    switch (tipo) {
      case "lead_criado": return <UserPlus {...props} />;
      case "status_mudou": return <ArrowRightLeft {...props} />;
      case "interesse_alterado": return <Heart {...props} />;
      case "followup_enviado": return <Clock {...props} />;
      case "transbordo_aberto":
      case "transbordo_fechado":
      case "transbordo_assumido":
      case "transbordo_devolvido": return <Headphones {...props} />;
      case "agendou": return <Calendar {...props} />;
      case "descartado": return <Trash2 {...props} />;
      case "reaberto": return <RotateCcw {...props} />;
      case "divergencia_ia_humano": return <AlertTriangle {...props} />;
      case "nota": return <FileText {...props} />;
      default: return <Clock {...props} />;
    }
  };

  const renderConteudoEvento = (ev: EventoTimeline) => {
    switch (ev.tipo) {
      case "lead_criado":
        return (
          <div>
            <span className="font-semibold" style={{ color: "var(--text-primary)" }}>Lead criado no sistema</span>
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>Primeiro contato registrado via automação.</p>
          </div>
        );
      case "status_mudou":
        return (
          <div>
            <span className="font-semibold" style={{ color: "var(--text-primary)" }}>Status alterado</span>:{" "}
            <span
              className="font-mono text-xs px-1.5 py-0.5 rounded"
              style={{ background: "rgba(255,255,255,0.06)", color: "var(--text-secondary)" }}
            >{ev.de}</span> &rarr;{" "}
            <span
              className="font-mono text-xs font-bold px-1.5 py-0.5 rounded"
              style={{ background: "var(--accent-primary-muted)", color: "var(--accent-primary)" }}
            >{ev.para}</span>
            <span className="ml-2 text-[10px] uppercase font-bold" style={{ color: "var(--text-muted)" }}>({ev.autor})</span>
          </div>
        );
      case "interesse_alterado":
        return (
          <div>
            <span className="font-semibold" style={{ color: "var(--text-primary)" }}>Interesse/Evento atualizado</span>
            {ev.detalhe && (
              <div className="text-xs mt-0.5" style={{ color: "var(--text-secondary)" }}>
                Evento: {ev.detalhe.evento || "—"} | Estilo: {ev.detalhe.estilo || "—"}
              </div>
            )}
          </div>
        );
      case "followup_enviado":
        return (
          <div>
            <span className="font-semibold" style={{ color: "var(--text-primary)" }}>Follow-up automático enviado</span>
            {ev.detalhe?.mensagem && (
              <p className="text-xs italic mt-0.5" style={{ color: "var(--text-muted)" }}>
                &quot;{ev.detalhe.mensagem}&quot;
              </p>
            )}
          </div>
        );
      case "transbordo_aberto":
        return (
          <div>
            <span className="font-semibold" style={{ color: "var(--accent-purple)" }}>Transbordo aberto</span>
            <p className="text-xs" style={{ color: "var(--text-secondary)" }}>Conversa encaminhada para atendimento humano.</p>
          </div>
        );
      case "transbordo_assumido":
        return (
          <div>
            <span className="font-semibold" style={{ color: "var(--accent-purple)" }}>Atendente assumiu a conversa</span>
            <p className="text-xs" style={{ color: "var(--text-secondary)" }}>IA pausada temporariamente (30 min).</p>
          </div>
        );
      case "transbordo_devolvido":
        return (
          <div>
            <span className="font-semibold" style={{ color: "var(--text-primary)" }}>Conversa devolvida para a IA</span>
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>Automação retomada com sucesso.</p>
          </div>
        );
      case "agendou":
        return (
          <div>
            <span className="font-semibold" style={{ color: "var(--accent-primary)" }}>Agendamento criado na WebLocação</span>
            {ev.detalhe && (
              <p className="text-xs font-mono mt-0.5" style={{ color: "var(--text-secondary)" }}>
                {ev.detalhe.tipo} - {ev.detalhe.data} às {ev.detalhe.hora}
              </p>
            )}
          </div>
        );
      case "descartado":
        return (
          <div>
            <span className="font-semibold" style={{ color: "var(--accent-coral)" }}>Lead descartado</span>
            {ev.motivo && <p className="text-xs mt-0.5" style={{ color: "var(--text-secondary)" }}>Motivo: {ev.motivo}</p>}
          </div>
        );
      case "divergencia_ia_humano":
        return (
          <div>
            <span className="font-semibold" style={{ color: "var(--accent-amber)" }}>Divergência de status (MV3)</span>
            <p className="text-xs" style={{ color: "var(--text-secondary)" }}>Movimentação humana recente mantida.</p>
          </div>
        );
      case "nota":
        return (
          <div>
            <span className="font-semibold" style={{ color: "var(--text-primary)" }}>Nota de Atendimento</span>
            {ev.motivo && <p className="text-xs mt-0.5" style={{ color: "var(--text-secondary)" }}>{ev.motivo}</p>}
          </div>
        );
      default:
        return <span className="font-semibold" style={{ color: "var(--text-primary)" }}>Evento de sistema</span>;
    }
  };

  return (
    <div className="glass-card p-4 space-y-4">
      {/* Header with Tags */}
      <div
        className="flex items-center justify-between pb-3"
        style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.06)" }}
      >
        <h3
          className="text-sm font-bold font-display"
          style={{ color: "var(--text-primary)" }}
        >
          Timeline de Eventos — {nomeLead}
        </h3>
        <div className="flex items-center gap-1.5">
          {tags.map((tag, idx) => (
            <span
              key={idx}
              className="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-semibold"
              style={{
                background: "rgba(255, 255, 255, 0.06)",
                color: "var(--text-secondary)",
                border: "1px solid rgba(255, 255, 255, 0.06)",
              }}
            >
              <Tag className="h-3 w-3" style={{ color: "var(--text-muted)" }} />
              {tag}
            </span>
          ))}
          {tags.length === 0 && (
            <span className="text-xs italic" style={{ color: "var(--text-muted)" }}>
              Sem tags
            </span>
          )}
        </div>
      </div>

      {/* Timeline */}
      <div
        className="relative pl-6 space-y-6"
        style={{
          /* Vertical teal line */
        }}
      >
        {/* Vertical line */}
        <div
          className="absolute left-2.5 top-2 bottom-2 w-0.5"
          style={{ background: "rgba(16, 185, 129, 0.2)" }}
        />

        {eventos.map((ev) => (
          <div key={ev.id} className="relative flex items-start gap-3 text-xs">
            {/* Icon dot */}
            <div
              className="absolute -left-6 top-0.5 flex h-5 w-5 items-center justify-center rounded-full"
              style={{
                background: "var(--bg-elevated)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
              }}
            >
              {renderIconeEvento(ev.tipo)}
            </div>

            {/* Event Content */}
            <div
              className="flex-1 rounded-lg p-2.5 space-y-1"
              style={{
                background: "rgba(255, 255, 255, 0.03)",
                border: "1px solid rgba(255, 255, 255, 0.04)",
              }}
            >
              <div className="flex items-center justify-between">
                {renderConteudoEvento(ev)}
                <span className="text-[10px] font-mono ml-2" style={{ color: "var(--text-muted)" }}>
                  {new Date(ev.criado_em).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>
            </div>
          </div>
        ))}

        {eventos.length === 0 && (
          <div className="py-6 text-center text-xs italic" style={{ color: "var(--text-muted)" }}>
            Nenhum evento registrado na timeline.
          </div>
        )}
      </div>
    </div>
  );
}
